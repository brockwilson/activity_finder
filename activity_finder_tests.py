import os
import activity_finder
import unittest
import tempfile

class ActivityFinderTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, activity_finder.app.config['DATABASE'] = tempfile.mkstemp()
        activity_finder.app.config['TESTING'] = True
        self.app = activity_finder.app.test_client()
        activity_finder.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(activity_finder.app.config['DATABASE'])

    def login(self, username, password):
        return self.app.post('/login', data=dict(
                username=username,
                password=password),
                             follow_redirects=True)
    
    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def test_empty_db(self):
        rv = self.app.get('/')
        assert 'No entries.' in rv.data

    def test_login_logout(self):
        rv = self.login('admin', 'default')
        assert 'You were logged in' in rv.data
        rv = self.logout()
        assert 'You were logged out' in rv.data
        rv = self.login('adminx', 'default')
        assert 'Invalid username' in rv.data
        rv = self.login('admin', 'defaultx')
        assert 'Invalid password' in rv.data

    def test_entries(self):
        self.login('admin', 'default')
        rv = self.app.post('/add', data=dict(
                title='<Hello>',
                description='<strong>HTML</strong> allowed here',
                address='blah blah blah',
                min_age='0',
                max_age='10',
                schedule='more blahs',
                fee='0'),
                           follow_redirects=True)
        assert 'No entries' not in rv.data
        assert '&lt;Hello&gt;' in rv.data
        assert '<strong>HTML</strong> allowed here' in rv.data


if __name__ == '__main__':
    unittest.main()
