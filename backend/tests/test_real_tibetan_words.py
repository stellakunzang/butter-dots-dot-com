"""
Pressure test with REAL Tibetan words

Based on Unicode encoding analysis and actual Tibetan vocabulary.
Tests our understanding of syllable structure before full implementation.
"""
import pytest


class TestSimpleWords:
    """Test basic Tibetan words - root + suffix patterns"""
    
    def test_bod_tibet(self):
        """བོད (bod - Tibet): root + vowel + suffix"""
        word = "བོད"
        # བ (U+0F56) = root
        # ོ (U+0F7C) = vowel o
        # ད (U+0F51) = suffix
        
        # Unicode verification
        assert ord(word[0]) == 0x0F56  # ba
        assert ord(word[1]) == 0x0F7C  # vowel o
        assert ord(word[2]) == 0x0F51  # da suffix
        
        # Should be VALID
        # TODO: Test with parser when implemented
    
    def test_lang(self):
        """ལང (lang): root + suffix"""
        word = "ལང"
        # ལ (U+0F63) = root
        # ང (U+0F44) = suffix
        
        assert ord(word[0]) == 0x0F63  # la root
        assert ord(word[1]) == 0x0F44  # nga suffix
        
        # Should be VALID


class TestWordsWithPrefixes:
    """Test prefix + root + suffix patterns"""
    
    def test_gang(self):
        """གང (gang): prefix + root"""
        word = "གང"
        # ག (U+0F42) = prefix
        # ང (U+0F44) = root
        
        assert ord(word[0]) == 0x0F42  # ga prefix
        assert ord(word[1]) == 0x0F44  # nga root
        
        # ga can prefix nga (not in invalid list)
        # Should be VALID
    
    def test_dbang_power(self):
        """དབང (dbang - power): prefix + root + suffix"""
        word = "དབང"
        # ད (U+0F51) = prefix
        # བ (U+0F56) = root (base form, no superscript)
        # ང (U+0F44) = suffix
        
        assert ord(word[0]) == 0x0F51  # da prefix
        assert ord(word[1]) == 0x0F56  # ba root
        assert ord(word[2]) == 0x0F44  # nga suffix
        
        # da can prefix ba (not in invalid list)
        # Should be VALID
    
    def test_dkar_white(self):
        """དཀར (dkar - white): prefix + root + suffix"""
        word = "དཀར"
        # ད (U+0F51) = prefix
        # ཀ (U+0F40) = root
        # ར (U+0F62) = suffix
        
        assert ord(word[0]) == 0x0F51  # da prefix
        assert ord(word[1]) == 0x0F40  # ka root
        assert ord(word[2]) == 0x0F62  # ra suffix
        
        # da can prefix ka (not in invalid list)
        # Should be VALID
    
    def test_gnyis_two(self):
        """གཉིས (gnyis - two): prefix + root + vowel + suffix"""
        word = "གཉིས"
        # ག (U+0F42) = prefix
        # ཉ (U+0F49) = root
        # ི (U+0F72) = vowel i
        # ས (U+0F66) = suffix
        
        assert ord(word[0]) == 0x0F42  # ga prefix
        assert ord(word[1]) == 0x0F49  # nya root
        assert ord(word[2]) == 0x0F72  # vowel i
        assert ord(word[3]) == 0x0F66  # sa suffix
        
        # ga can prefix nya (not in invalid list)
        # Should be VALID


class TestInvalidPrefixes:
    """Test prefix combinations that should be INVALID"""
    
    def test_ga_ka_invalid(self):
        """གཀ (ga + ka): INVALID - ga cannot prefix ka"""
        word = "གཀ"
        # ག (U+0F42) = would be prefix
        # ཀ (U+0F40) = would be root
        
        assert ord(word[0]) == 0x0F42  # ga
        assert ord(word[1]) == 0x0F40  # ka
        
        # ga CANNOT prefix ka (in invalid list)
        # Should be INVALID
    
    def test_ga_pa_invalid(self):
        """གཔ (ga + pa): INVALID - ga cannot prefix pa"""
        word = "གཔ"
        assert ord(word[0]) == 0x0F42  # ga
        assert ord(word[1]) == 0x0F54  # pa
        
        # ga CANNOT prefix pa (in invalid list)
        # Should be INVALID
    
    def test_da_ya_invalid(self):
        """དཡ (da + ya): INVALID - da cannot prefix ya"""
        word = "དཡ"
        assert ord(word[0]) == 0x0F51  # da
        assert ord(word[1]) == 0x0F61  # ya
        
        # da CANNOT prefix ya (in invalid list)
        # Should be INVALID


class TestSuperscriptWords:
    """Test words with superscripts (ra-mgo, la-mgo, sa-mgo)"""
    
    def test_rgyal_king(self):
        """རྒྱལ (rgyal - king): superscript + root + subscript + suffix"""
        word = "རྒྱལ"
        # ར (U+0F62) = superscript ra-mgo
        # ྒ (U+0F92) = root ga (subjoined form!)
        # ྱ (U+0FB1) = subscript ya-btags
        # ལ (U+0F63) = suffix la
        
        assert ord(word[0]) == 0x0F62  # base ra = superscript
        assert ord(word[1]) == 0x0F92  # subjoined ga = root
        assert ord(word[2]) == 0x0FB1  # subjoined ya = subscript
        assert ord(word[3]) == 0x0F63  # base la = suffix
        
        # Verify it uses subjoined forms
        assert 0x0F90 <= ord(word[1]) <= 0x0FBC  # root is subjoined
        assert 0x0F90 <= ord(word[2]) <= 0x0FBC  # subscript is subjoined
        
        # Should be VALID
    
    def test_sgrub_accomplish(self):
        """སྒྲུབ (sgrub): superscript + root + subscript + vowel + suffix"""
        word = "སྒྲུབ"
        # ས (U+0F66) = superscript sa-mgo
        # ྒ (U+0F92) = root ga (subjoined)
        # ྲ (U+0FB2) = subscript ra-btags
        # ུ (U+0F74) = vowel u
        # བ (U+0F56) = suffix ba
        
        assert ord(word[0]) == 0x0F66  # base sa = superscript
        assert ord(word[1]) == 0x0F92  # subjoined ga = root
        assert ord(word[2]) == 0x0FB2  # subjoined ra = subscript
        assert ord(word[3]) == 0x0F74  # vowel u
        assert ord(word[4]) == 0x0F56  # base ba = suffix
        
        # Should be VALID


class TestComplexWords:
    """Test complex words with all 7 components"""
    
    def test_bsgrubs_accomplished(self):
        """བསྒྲུབས (bsgrubs): All 7 components!"""
        word = "བསྒྲུབས"
        # བ (U+0F56) = prefix ba
        # ས (U+0F66) = superscript sa-mgo
        # ྒ (U+0F92) = root ga (subjoined)
        # ྲ (U+0FB2) = subscript ra-btags
        # ུ (U+0F74) = vowel u
        # བ (U+0F56) = suffix ba
        # ས (U+0F66) = post-suffix sa
        
        assert ord(word[0]) == 0x0F56  # prefix
        assert ord(word[1]) == 0x0F66  # superscript
        assert ord(word[2]) == 0x0F92  # root (subjoined)
        assert ord(word[3]) == 0x0FB2  # subscript (subjoined)
        assert ord(word[4]) == 0x0F74  # vowel
        assert ord(word[5]) == 0x0F56  # suffix
        assert ord(word[6]) == 0x0F66  # post-suffix
        
        # Structure: PREFIX + SUPERSCRIPT + ROOT + SUBSCRIPT + VOWEL + SUFFIX + POST-SUFFIX
        # Should be VALID


class TestSubscriptCombinations:
    """Test subscript (ya-btags, ra-btags, la-btags, wa-zur) patterns"""
    
    def test_kya(self):
        """ཀྱ (kya): root + ya-btags"""
        word = "ཀྱ"
        # ཀ (U+0F40) = root ka
        # ྱ (U+0FB1) = subscript ya-btags
        
        assert ord(word[0]) == 0x0F40  # ka root
        assert ord(word[1]) == 0x0FB1  # ya subscript
        
        # ka can take ya subscript
        # Should be VALID
    
    def test_kra(self):
        """ཀྲ (kra): root + ra-btags"""
        word = "ཀྲ"
        # ཀ (U+0F40) = root ka
        # ྲ (U+0FB2) = subscript ra-btags
        
        assert ord(word[0]) == 0x0F40  # ka root
        assert ord(word[1]) == 0x0FB2  # ra subscript
        
        # ka can take ra subscript
        # Should be VALID
    
    def test_kla(self):
        """ཀླ (kla): root + la-btags"""
        word = "ཀླ"
        # ཀ (U+0F40) = root ka
        # ླ (U+0FB3) = subscript la-btags
        
        assert ord(word[0]) == 0x0F40  # ka root
        assert ord(word[1]) == 0x0FB3  # la subscript
        
        # ka can take la subscript
        # Should be VALID
    
    def test_kwa(self):
        """ཀྭ (kwa): root + wa-zur"""
        word = "ཀྭ"
        # ཀ (U+0F40) = root ka
        # ྭ (U+0FAD) = subscript wa-zur
        
        assert ord(word[0]) == 0x0F40  # ka root
        assert ord(word[1]) == 0x0FAD  # wa subscript
        
        # ka can take wa subscript
        # Should be VALID


class TestUnicodeRanges:
    """Verify our understanding of Unicode ranges"""
    
    def test_base_consonant_range(self):
        """Base consonants are U+0F40 - U+0F6C"""
        # Used for: prefix, superscript, suffix, post-suffix, standalone root
        assert 0x0F40 <= ord('ཀ') <= 0x0F6C  # ka
        assert 0x0F40 <= ord('ག') <= 0x0F6C  # ga
        assert 0x0F40 <= ord('ད') <= 0x0F6C  # da
        assert 0x0F40 <= ord('བ') <= 0x0F6C  # ba
        assert 0x0F40 <= ord('མ') <= 0x0F6C  # ma
        assert 0x0F40 <= ord('ར') <= 0x0F6C  # ra
        assert 0x0F40 <= ord('ལ') <= 0x0F6C  # la
        assert 0x0F40 <= ord('ས') <= 0x0F6C  # sa
    
    def test_subjoined_consonant_range(self):
        """Subjoined consonants are U+0F90 - U+0FBC"""
        # Used for: root under superscript, subscripts
        assert 0x0F90 <= ord('ྐ') <= 0x0FBC  # subjoined ka
        assert 0x0F90 <= ord('ྒ') <= 0x0FBC  # subjoined ga
        assert 0x0F90 <= ord('ྱ') <= 0x0FBC  # ya-btags
        assert 0x0F90 <= ord('ྲ') <= 0x0FBC  # ra-btags
        assert 0x0F90 <= ord('ླ') <= 0x0FBC  # la-btags
        assert 0x0F90 <= ord('ྭ') <= 0x0FBC  # wa-zur
    
    def test_vowel_range(self):
        """Vowels are U+0F71 - U+0F7C"""
        assert 0x0F71 <= ord('ི') <= 0x0F7C  # i
        assert 0x0F71 <= ord('ུ') <= 0x0F7C  # u
        assert 0x0F71 <= ord('ེ') <= 0x0F7C  # e
        assert 0x0F71 <= ord('ོ') <= 0x0F7C  # o
    
    def test_subjoined_offset(self):
        """Subjoined = Base + 0x50"""
        # ག (ga) base = U+0F42
        # ྒ (ga) subjoined = U+0F92
        ga_base = ord('ག')
        ga_subjoined = ord('ྒ')
        assert ga_subjoined == ga_base + 0x50
        
        # ཀ (ka) base = U+0F40
        # ྐ (ka) subjoined = U+0F90
        ka_base = ord('ཀ')
        ka_subjoined = ord('ྐ')
        assert ka_subjoined == ka_base + 0x50
