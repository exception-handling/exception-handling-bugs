import unittest
import unittest.mock

from miner_py_src.call_graph import CFG, generate_cfg


cfg_mock = {
    "teste.raise_exception": {
        "calls": [],
        "called_by": ["teste.except_caller"]
    },
    "teste.except_caller": {
        "calls": ["teste.raise_exception"],
        "called_by": ["teste.except_caught"]
    }
}


class TestCFG(unittest.TestCase):
    def test_flow_exception_handled(self):
        graph = CFG(cfg_mock,
                    {'teste.except_caller': ["ValueError"]})

        actual = graph.get_uncaught_exceptions('teste.raise_exception',
                                               ['ValueError'])
        expected = {}

        self.assertEqual(actual, expected)

    def test_flow_exception_unhandled(self):
        graph = CFG(cfg_mock,
                    {'teste.except_caller': ["ValueError"]})

        actual = graph.get_uncaught_exceptions('teste.raise_exception',
                                               ['ValueError', 'NewException'])

        expected = {'teste.except_caller': ['NewException']}

        self.assertEqual(actual, expected)

    def test_no_exception_handlers(self):
        graph = CFG(cfg_mock, {})

        actual = graph.get_uncaught_exceptions('teste.raise_exception',
                                               ['ValueError', 'NewException'])

        expected = {'teste.except_caller': ['ValueError', 'NewException']}

        self.assertEqual(actual, expected)


class TestGenerateCFG(unittest.TestCase):
    @unittest.mock.patch('os.makedirs')
    @unittest.mock.patch('os.chdir')
    @unittest.mock.patch('glob.iglob', return_value=['teste'])
    @unittest.mock.patch('subprocess.run', return_value=unittest.mock.Mock(returncode=0))
    @unittest.mock.patch('json.load')
    @unittest.mock.patch('miner_py_src.call_graph.open', return_value=unittest.mock.Mock())
    @unittest.mock.patch('tqdm.tqdm.write', return_value=unittest.mock.Mock())
    def test_generate_cfg(self,
                          tqdm_mock,
                          open_mock,
                          json_load_mock,
                          run_mock,
                          iglob_mock,
                          chdir_mock,
                          makedirs_mock,
                          ):

        cfg_mock = {
            "...teste": ["...teste.ClassB.method_name", "...teste.ClassA.method_name"],
            "...teste.ClassA.method_name": [],
            "...teste.ClassB.method_name": [],
            "...teste.raise_exception": [],
            "...teste.uncaught_exception": ["...teste.raise_exception"]
        }

        json_load_mock.return_value = cfg_mock

        cfg = generate_cfg('teste', 'teste')

        self.assertIsNotNone(cfg)

        self.assertEquals(cfg, {
            "...teste": {
                "calls": [
                    "...teste.ClassB.method_name",
                    "...teste.ClassA.method_name"
                ],
                "called_by": []
            },
            "...teste.ClassB.method_name": {
                "calls": [],
                "called_by": [
                    "...teste"
                ]
            },
            "...teste.ClassA.method_name": {
                "calls": [],
                "called_by": [
                    "...teste"
                ]
            },
            "...teste.raise_exception": {
                "calls": [],
                "called_by": [
                    "...teste.uncaught_exception"
                ]
            },
            "...teste.uncaught_exception": {
                "calls": [
                    "...teste.raise_exception"
                ],
                "called_by": []
            }
        })
