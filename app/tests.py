#!/usr/bin/env python

import os
import unittest

class TestCase(unittest.TestCase):
    
    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
