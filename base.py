
import ast
import astor
import json
import logging
import collections
from os import path

json_file = path.dirname(__file__) + "/api_mapping.json"
with open(json_file, 'r') as file:
    API_MAPPING = json.load(file)



class BaseTransformer(ast.NodeTransformer):
    def __init__(self, root, file, imports_map):
        self.root = root
        self.file = file
        self.file_name = path.basename(file)
        self.imports_map = imports_map
        self.torch_api_count = 0
        self.success_api_count = 0
        self.root = root
        self.log_msg = []
        self.node_stack = []
        self.scope_stack = []
        self.scope_insert_lines = collections.defaultdict(lambda: dict())
    
    def transform(self):
        self.visit(self.root)
        self.insert_scope()

    def visit(self, node):
        self.node_stack.append(node)
        node = super(BaseTransformer, self).visit(node)
        self.node_stack.pop()
        return node

    def record_scope(self, scope_node, index, node):
        if node is None:
            return
        if not isinstance(node, list):
            node = [node]
        if index in self.scope_insert_lines[scope_node]:
            self.scope_insert_lines[scope_node][index].extend(node)
        else:
            self.scope_insert_lines[scope_node][index] = node
            
    def insert_scope(self):
        # if multiple line, insert into scope node only One time
        for scope_node in self.scope_insert_lines:
            insert_lines = self.scope_insert_lines[scope_node]
            insert_lines = sorted(insert_lines.items(), 
                                  key = lambda x:x[0], 
                                  reverse = True)
            for index, lines in insert_lines:
                for line in lines[::-1]:
                    scope_node.body.insert(index, line)


    def log_info(self, msg, file=None, line=None):
        if file:
            if line:
                msg = "[{}:{}] {}".format(file, line, msg)
            else:
                msg = "[{}] {}".format(file, msg)
        else:
            msg = "{}".format(msg)
        logging.info(msg)
        self.log_msg.append(msg)

    def get_full_attr(self, node):
        if isinstance(node, ast.Attribute):
            return self.get_full_attr(node.value) + '.' + node.attr
        elif isinstance(node, ast.Name):
            return node.id
        else:
            return 'TensorMethod'

    def get_full_api_from_node(self, node):
        full_attr = self.get_full_attr(node)
        attr_list = full_attr.split('.')
        old_module = attr_list[0]
        if old_module in self.imports_map[self.file]:
            new_module = self.imports_map[self.file][old_module]
            attr_list[0] = new_module
            torch_api = '.'.join(attr_list)
            return torch_api
        else:
            return None


class BaseMatcher(object):
    def __init__(self, api_mapping):
        self.api_mapping = api_mapping

    def get_paddle_api(self):
        if 'paddle_api' in self.api_mapping:
            return self.api_mapping['paddle_api']
        return None

    def args_to_kwargs(self, args, kwargs):
        args_list = self.api_mapping.get('args_list') or []
        assert len(args) <= len(args_list)

        new_kwargs = {}
        for i, node in enumerate(args):
            k = args_list[i]
            v = astor.to_source(node).strip('\n')
            new_kwargs[k] = v
        
        for node in kwargs:
            k = node.arg
            v = astor.to_source(node.value).strip('\n')
            new_kwargs[k] = v

        return new_kwargs
    
    def kwargs_to_str(self, kwargs):
        str_list = []
        for k, v in kwargs.items():
            str_list.append('{}={}'.format(k, v))

        return ', '.join(str_list)

    def get_paddle_nodes(self, args, kwargs):
        new_kwargs = self.args_to_kwargs(args, kwargs)
        new_code = self.generate_code(new_kwargs)
        if new_code:
            return ast.parse(new_code).body
        return None

    def generate_code(self, kwargs):
        return None