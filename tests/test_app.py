import os
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        app.DB_PATH = Path(self.tmp.name) / 'test.db'
        app.init_db()

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_update_delete(self):
        task = app.create_task({'title': 'Study for exam', 'course': 'CS', 'priority': 'high', 'due_date': '2026-12-10'})
        self.assertEqual(task['status'], 'todo')
        self.assertEqual(app.summary()['total'], 1)
        self.assertEqual(len(app.list_tasks({'priority': 'high'})), 1)
        self.assertEqual(len(app.list_tasks({'q': 'exam'})), 1)
        changed = app.update_task(task['id'], {'status': 'done'})
        self.assertEqual(changed['status'], 'done')
        self.assertEqual(app.summary()['completed'], 1)
        self.assertTrue(app.delete_task(task['id']))
        self.assertIsNone(app.get_task(task['id']))

    def test_validation(self):
        for invalid in ({'title': ''}, {'title': 'X', 'due_date': '2026-02-30'}, {'title': 'X', 'priority': 'urgent'}, {'title': 'X', 'status': 'unknown'}, {'title': '<' * 121}):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                app.create_task(invalid)
        with self.assertRaises(ValueError):
            app.update_task(999, {'bad': 'field'})

    def test_search_literal_wildcards(self):
        app.create_task({'title': '100% complete'})
        app.create_task({'title': 'Read chapter'})
        self.assertEqual(len(app.list_tasks({'q': '%'})), 1)


if __name__ == '__main__':
    unittest.main()
