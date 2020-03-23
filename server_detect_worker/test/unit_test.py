from ..app import app
import random, string

class mock_response:  
    def __init__(self, pheaders, pstatus_code, pbody):
        self.headers = pheaders
        self.status_code = pstatus_code
        self.body = pbody

def test_find_server_type_in_body_true():
    server_type = generate_random_word(random.randrange(1, 10))
    body = generate_random_word(random.randrange(1, 100)) +  server_type + generate_random_word(random.randrange(1, 100))
    assert app.find_server_type_in_body(server_type, body)

def test_find_server_type_in_body_false():
    server_type = generate_random_word(random.randrange(1, 10)) + '1'
    body = generate_random_word(random.randrange(20, 100))
    assert app.find_server_type_in_body(server_type, body) == False

def find_server_type_in_header_true():
    server_type = 'test_server' 
    response = mock_response({'Server':'test_server'},'not_test_server', 200)
    assert app.find_server_type_in_header(server_type, response)

def find_server_type_in_header_false():
    server_type = 'test_server' 
    response = mock_response({'asd':'asd'},'not_test_server', 200)
    assert app.find_server_type_in_header(server_type, response) == False

def generate_random_word(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


