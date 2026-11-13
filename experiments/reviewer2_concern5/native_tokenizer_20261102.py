"""Vocabulary-only tokenizer using the installed llama.cpp C ABI; no inference context.

ABI pinned to the installed server build 39febd2ad, include/llama.h.
No backend initialization, tensor evaluation, sampling, or GPU context is used.
"""
import ctypes as C
import os
import hashlib
from pathlib import Path

LIBDIR = Path('C:/Users/isegu/AppData/Local/Programs/Ollama/lib/ollama')


class ModelParams(C.Structure):
    _fields_ = [('devices',C.c_void_p),('tensor_buft_overrides',C.c_void_p),
        ('n_gpu_layers',C.c_int32),('split_mode',C.c_int),('load_mode',C.c_int),
        ('lazy_mode',C.c_int),('main_gpu',C.c_int32),('tensor_split',C.c_void_p),
        ('progress_callback',C.c_void_p),('progress_callback_user_data',C.c_void_p),
        ('kv_overrides',C.c_void_p),('vocab_only',C.c_bool),('check_tensors',C.c_bool),
        ('use_extra_bufts',C.c_bool),('no_host',C.c_bool),('no_alloc',C.c_bool),
        ('load_mtp',C.c_bool)]


class Vocabulary:
    def __init__(self,path,expected_size):
        assert C.sizeof(ModelParams)==80 and ModelParams.vocab_only.offset==72
        if hashlib.sha256((LIBDIR/'libllama.dll').read_bytes()).hexdigest()!='a9ccb9ae84f200579d1103a6d7cb67eb2e79342961497a74dc35d9c87894d9d9':
            raise ValueError('Native library changed; recheck its exact ABI and tokenizer before use.')
        self.dll_dir=os.add_dll_directory(str(LIBDIR))
        self.lib=C.CDLL(str(LIBDIR/'libllama.dll'))
        self.lib.llama_version.restype=C.c_char_p
        if self.lib.llama_version()!=b'0.8.0-dev':
            raise ValueError('Installed ABI changed; inspect the exact header before use.')
        self.lib.llama_model_default_params.restype=ModelParams
        self.lib.llama_model_load_from_file.argtypes=[C.c_char_p,ModelParams]
        self.lib.llama_model_load_from_file.restype=C.c_void_p
        self.lib.llama_model_free.argtypes=[C.c_void_p]
        self.lib.llama_model_get_vocab.argtypes=[C.c_void_p]
        self.lib.llama_model_get_vocab.restype=C.c_void_p
        self.lib.llama_vocab_n_tokens.argtypes=[C.c_void_p]
        self.lib.llama_vocab_n_tokens.restype=C.c_int32
        self.lib.llama_tokenize.argtypes=[C.c_void_p,C.c_char_p,C.c_int32,
                                         C.POINTER(C.c_int32),C.c_int32,C.c_bool,C.c_bool]
        self.lib.llama_tokenize.restype=C.c_int32
        self.logs=[]
        log_type=C.CFUNCTYPE(None,C.c_int,C.c_char_p,C.c_void_p)
        self.log_callback=log_type(lambda level,message,unused:self.logs.append(message.decode('utf-8',errors='replace')))
        self.lib.llama_log_set.argtypes=[log_type,C.c_void_p]
        self.lib.llama_log_set(self.log_callback,None)
        params=self.lib.llama_model_default_params()
        assert params.n_gpu_layers in [-1,0,99,999] and params.main_gpu==0
        params.n_gpu_layers=0
        params.vocab_only=True
        params.no_alloc=True
        self.model=self.lib.llama_model_load_from_file(str(path).encode(),params)
        if not self.model:raise ValueError('Vocabulary-only load failed: '+''.join(self.logs)[-1000:])
        self.vocab=self.lib.llama_model_get_vocab(self.model)
        assert self.lib.llama_vocab_n_tokens(self.vocab)==expected_size
        assert any('vocab only - skipping tensors' in message for message in self.logs)

    def encode(self,text):
        data=text.encode('utf-8')
        needed=self.lib.llama_tokenize(self.vocab,data,len(data),None,0,True,True)
        if needed>0:raise ValueError('Unexpected token buffer request')
        buffer=(C.c_int32*(-needed))()
        count=self.lib.llama_tokenize(self.vocab,data,len(data),buffer,len(buffer),True,True)
        assert count>=0 and count==len(buffer)
        return list(buffer)

    def close(self):
        if self.model:
            self.lib.llama_model_free(self.model)
            self.model=None
