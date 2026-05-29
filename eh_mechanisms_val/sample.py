"def process_file(self, *, path, parent_fd, name, st, cache, flags=flags_normal, last_try=False):
        with self.create_helper(path, st, None) as (item, status, hardlinked, hl_chunks):  # no status yet
            with OsOpen(path=path, parent_fd=parent_fd, name=name, flags=flags, noatime=True) as fd:
                with backup_io(""fstat""):
                    st = stat_update_check(st, os.fstat(fd))
                item.update(self.metadata_collector.stat_simple_attrs(st))
                is_special_file = is_special(st.st_mode)
                if is_special_file:
                    # we process a special file like a regular file. reflect that in mode,
                    # so it can be extracted / accessed in FUSE mount like a regular file.
                    # this needs to be done early, so that part files also get the patched mode.
                    item.mode = stat.S_IFREG | stat.S_IMODE(item.mode)
                # we begin processing chunks now (writing or incref'ing them to the repository),
                # which might require cleanup (see except-branch):
                try:
                    if hl_chunks is not None:  # create_helper gave us chunks from a previous hardlink
                        item.chunks = []
                        for chunk_id, chunk_size in hl_chunks:
                            # process one-by-one, so we will know in item.chunks how far we got
                            chunk_entry = cache.chunk_incref(chunk_id, self.stats)
                            item.chunks.append(chunk_entry)
                    else:  # normal case, no ""2nd+"" hardlink
                        if not is_special_file:
                            hashed_path = safe_encode(os.path.join(self.cwd, path))
                            started_hashing = time.monotonic()
                            path_hash = self.key.id_hash(hashed_path)
                            self.stats.hashing_time += time.monotonic() - started_hashing
                            known, ids = cache.file_known_and_unchanged(hashed_path, path_hash, st)
                        else:
                            # in --read-special mode, we may be called for special files.
                            # there should be no information in the cache about special files processed in
                            # read-special mode, but we better play safe as this was wrong in the past:
                            hashed_path = path_hash = None
                            known, ids = False, None
                        if ids is not None:
                            # Make sure all ids are available
                            for id_ in ids:
                                if not cache.seen_chunk(id_):
                                    # cache said it is unmodified, but we lost a chunk: process file like modified
                                    status = ""M""
                                    break
                            else:
                                item.chunks = []
                                for chunk_id in ids:
                                    # process one-by-one, so we will know in item.chunks how far we got
                                    chunk_entry = cache.chunk_incref(chunk_id, self.stats)
                                    item.chunks.append(chunk_entry)
                                status = ""U""  # regular file, unchanged
                        else:
                            status = ""M"" if known else ""A""  # regular file, modified or added
                        self.print_file_status(status, path)
                        # Only chunkify the file if needed
                        changed_while_backup = False
                        if ""chunks"" not in item:
                            with backup_io(""read""):
                                self.process_file_chunks(
                                    item,
                                    cache,
                                    self.stats,
                                    self.show_progress,
                                    backup_io_iter(self.chunker.chunkify(None, fd)),
                                )
                                self.stats.chunking_time = self.chunker.chunking_time
                            if not is_win32:  # TODO for win32
                                with backup_io(""fstat2""):
                                    st2 = os.fstat(fd)
                                # special files:
                                # - fifos change naturally, because they are fed from the other side. no problem.
                                # - blk/chr devices don't change ctime anyway.
                                changed_while_backup = not is_special_file and st.st_ctime_ns != st2.st_ctime_ns
                            if changed_while_backup:
                                # regular file changed while we backed it up, might be inconsistent/corrupt!
                                if last_try:
                                    status = ""C""  # crap! retries did not help.
                                else:
                                    raise BackupError(""file changed while we read it!"")
                            if not is_special_file and not changed_while_backup:
                                # we must not memorize special files, because the contents of e.g. a
                                # block or char device will change without its mtime/size/inode changing.
                                # also, we must not memorize a potentially inconsistent/corrupt file that
                                # changed while we backed it up.
                                cache.memorize_file(hashed_path, path_hash, st, [c.id for c in item.chunks])
                        self.stats.files_stats[status] += 1  # must be done late
                        if not changed_while_backup:
                            status = None  # we already called print_file_status
                    self.stats.nfiles += 1
                    item.update(self.metadata_collector.stat_ext_attrs(st, path, fd=fd))
                    item.get_size(memorize=True)
                    return status
                except BackupOSError:
                    # Something went wrong and we might need to clean up a bit.
                    # Maybe we have already incref'ed some file content chunks in the repo -
                    # but we will not add an item (see add_item in create_helper) and thus
                    # they would be orphaned chunks in case that we commit the transaction.
                    for chunk in item.get(""chunks"", []):
                        cache.chunk_decref(chunk.id, self.stats, wait=False)
                    # Now that we have cleaned up the chunk references, we can re-raise the exception.
                    # This will skip processing of this file, but might retry or continue with the next one.
                    raise"