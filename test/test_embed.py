#!/usr/bin/env python
import unittest

from sigtools.signatures import embed, IncompatibleSignatures
from sigtools.test import s
from test.util import sigtester

@sigtester
def embed_noshare_tests(self, result, *signatures):
    assert len(signatures) >= 2
    sigs = [s(sig) for sig in signatures]
    self.assertSigsEqual(
        embed(*sigs), s(result)
        )

@embed_noshare_tests
class EmbedNoShareTests(object):
    passthrough_pos = '<a>', '*args, **kwargs', '<a>'
    passthrough_pok = 'a', '*args, **kwargs', 'a'
    passthrough_kwo = '*, a', '*args, **kwargs', '*, a'

    add_pos_pos = '<a>, <b>', '<a>, *args, **kwargs', '<b>'
    add_pos_pok = '<a>, b', '<a>, *args, **kwargs', 'b'
    add_pos_kwo = '<a>, *, b', '<a>, *args, **kwargs', '*, b'

    add_pok_pos = '<a>, <b>', 'a, *args, **kwargs', '<b>'
    add_pok_pok = 'a, b', 'a, *args, **kwargs', 'b'
    add_pok_kwo = 'a, *, b', 'a, *args, **kwargs', '*, b'

    add_kwo_pos = '<b>, *, a', '*args, a, **kwargs', '<b>'
    add_kwo_pok = 'b, *, a', '*args, a, **kwargs', 'b'
    add_kwo_kwo = '*, a, b', '*args, a, **kwargs', '*, b'

    conv_pok_pos = '<a>', '*args', 'a'
    conv_pok_kwo = '*, a', '**kwargs', 'a'

@sigtester
def embed_noshare_raise_tests(self, *signatures):
    assert len(signatures) >= 2
    sigs = [s(sig) for sig in signatures]
    try:
        embed(*sigs)
    except IncompatibleSignatures as e:
        str(e)
    else:
        self.fail('IncompatibleSignatures not raised when merging '
            + ' '.join(str(sig) for sig in sigs))

@embed_noshare_raise_tests
class EmbedRaisesTests(object):
    no_placeholders_pos = '', '<a>'
    no_placeholders_pok = '', 'a'
    no_placeholders_kwo = '', '*, a'

    no_args_pos = '**kwargs', '<a>'

    dup_pos_pos = '<a>, *args, **kwargs', '<a>'

@sigtester
def embed_tests(self, result, share, *signatures):
    assert len(signatures) >= 2
    sigs = [s(sig) for sig in signatures]
    self.assertSigsEqual(
        embed(*sigs, share=share), s(result)
        )

@embed_tests
class EmbedTests(object):
    share_self = 'self, *, b', ['self'], 'self, *args, **kwargs', 'self, *, b'

    share_kwarg = '*, a', ['a'], '*args, a, **kwargs', '*, a'

if __name__ == '__main__':
    unittest.main()
