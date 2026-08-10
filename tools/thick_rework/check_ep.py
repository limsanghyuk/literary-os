# -*- coding: utf-8 -*-
"""사용법: python3 check_ep.py <작품명> <회차2자리>   (회차 단위 selfcheck)"""
import sys,os,shutil,subprocess,tempfile
BASE='/sessions/compassionate-eager-lovelace/mnt/claude'
W,EP=sys.argv[1],sys.argv[2]
f='%s/rework/%s/out/%s_%s.thick_sequence.jsonl'%(BASE,W,W,EP)
d=tempfile.mkdtemp(); shutil.copy(f,d)
subprocess.call([sys.executable,BASE+'/thick_directive/selfcheck.py',d,BASE+'/thick_directive/stock300.json'])
