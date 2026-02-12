"""
Tests for Tibetan Stacking Rules

Tests the data and lookup functions in rules/stacking.py:
- Valid component sets (prefixes, superscripts, subscripts, suffixes)
- Prefix + root combination validation
- Superscript + root combination validation
- Subscript + root combination validation

Based on traditional Tibetan grammar rules and linguistic research.
"""
import pytest


class TestPrefixRules:
    """Test prefix validation rules"""
    
    def test_valid_prefixes_exist(self):
        """5 letters can be prefixes: ga, da, ba, ma, achung"""
        from app.spellcheck.rules.stacking import VALID_PREFIXES
        
        assert len(VALID_PREFIXES) == 5
        assert "ག" in VALID_PREFIXES  # ga
        assert "ད" in VALID_PREFIXES  # da
        assert "བ" in VALID_PREFIXES  # ba
        assert "མ" in VALID_PREFIXES  # ma
        assert "འ" in VALID_PREFIXES  # achung
    
    def test_ga_prefix_valid_combinations(self):
        """ga (ག) can prefix certain letters"""
        from app.spellcheck.rules.stacking import is_valid_prefix_root
        
        # Valid combinations (from VBA research)
        assert is_valid_prefix_root("ག", "ཡ") is True  # ga-ya
        assert is_valid_prefix_root("ག", "ཉ") is True  # ga-nya
        assert is_valid_prefix_root("ག", "ད") is True  # ga-da
        assert is_valid_prefix_root("ག", "ང") is True  # ga-nga VALID
        
        # Invalid combinations (from VBA line 334)
        # ga CANNOT prefix: ka, kha, cha, ja, tha, tsa, pa, pha, dza, wa, ha
        assert is_valid_prefix_root("ག", "ཀ") is False  # ga-ka invalid
        assert is_valid_prefix_root("ག", "པ") is False  # ga-pa invalid
    
    def test_da_prefix_valid_combinations(self):
        """da (ད) can prefix certain letters"""
        from app.spellcheck.rules.stacking import is_valid_prefix_root
        
        # Valid combinations (from VBA line 334)
        assert is_valid_prefix_root("ད", "ཀ") is True  # da-ka (དཀར dkar)
        assert is_valid_prefix_root("ད", "ག") is True  # da-ga (དགའ dga')
        assert is_valid_prefix_root("ད", "ང") is True  # da-nga (དངོས dngos)
        
        # Invalid combinations (from VBA line 334)
        assert is_valid_prefix_root("ད", "ཁ") is False  # da-kha invalid
        assert is_valid_prefix_root("ད", "ཡ") is False  # da-ya invalid
    
    def test_non_prefix_letter(self):
        """Letters that are not prefixes should fail"""
        from app.spellcheck.rules.stacking import is_valid_prefix_root
        
        # la (ལ) is NOT a valid prefix
        assert is_valid_prefix_root("ལ", "ཀ") is False
        assert is_valid_prefix_root("ས", "ཀ") is False  # sa not a prefix
    
    def test_prefix_with_empty_base(self):
        """Prefix with empty base should be invalid"""
        from app.spellcheck.rules.stacking import is_valid_prefix_root
        
        assert is_valid_prefix_root("ག", "") is False
        assert is_valid_prefix_root("", "ཀ") is False


class TestSuperscriptRules:
    """Test superscript (ra-mgo, la-mgo, sa-mgo) validation"""
    
    def test_valid_superscripts_exist(self):
        """Only 3 letters can be superscripts"""
        from app.spellcheck.rules.stacking import VALID_SUPERSCRIPTS
        
        assert len(VALID_SUPERSCRIPTS) == 3
        assert "ར" in VALID_SUPERSCRIPTS  # ra-mgo
        assert "ལ" in VALID_SUPERSCRIPTS  # la-mgo  
        assert "ས" in VALID_SUPERSCRIPTS  # sa-mgo
    
    def test_ra_mgo_valid_combinations(self):
        """ra-mgo (ར) can superscript certain letters"""
        from app.spellcheck.rules.stacking import is_valid_superscript_root
        
        # Valid combinations (from authoritative valid stacks list)
        assert is_valid_superscript_root("ར", "ཀ") is True  # རྐ rka
        assert is_valid_superscript_root("ར", "ག") is True  # རྒ rga
        assert is_valid_superscript_root("ར", "ང") is True  # རྔ rnga - VALID per stacks list
        
        # Invalid combinations (not in valid stacks list)
        # TODO: Add examples of invalid ra-mgo combinations
    
    def test_la_mgo_valid_combinations(self):
        """la-mgo (ལ) can superscript certain letters"""
        from app.spellcheck.rules.stacking import is_valid_superscript_root
        
        # Valid combinations (from authoritative valid stacks list)
        assert is_valid_superscript_root("ལ", "ཀ") is True  # ལྐ lka
        assert is_valid_superscript_root("ལ", "ག") is True  # ལྒ lga
        assert is_valid_superscript_root("ལ", "ང") is True  # ལྔ lnga - VALID per stacks list
        
        # Invalid combinations (not in valid stacks list)
        # TODO: Add examples of invalid la-mgo combinations
    
    def test_sa_mgo_valid_combinations(self):
        """sa-mgo (ས) can superscript certain letters"""
        from app.spellcheck.rules.stacking import is_valid_superscript_root
        
        # Valid combinations (from authoritative valid stacks list)
        assert is_valid_superscript_root("ས", "ཀ") is True  # སྐ ska
        assert is_valid_superscript_root("ས", "ག") is True  # སྒ sga
        assert is_valid_superscript_root("ས", "ང") is True  # སྔ snga - VALID per stacks list
        
        # Invalid combinations (not in valid stacks list)
        # TODO: Add examples of invalid sa-mgo combinations
    
    def test_non_superscript_letter(self):
        """Non-superscript letters should fail"""
        from app.spellcheck.rules.stacking import is_valid_superscript_root
        
        # ga (ག) cannot be a superscript
        assert is_valid_superscript_root("ག", "ཀ") is False


class TestSubscriptRules:
    """Test subscript (ya-btags, ra-btags, la-btags, wa-zur) validation"""
    
    def test_valid_subscripts_exist(self):
        """Only 4 letters can be subscripts"""
        from app.spellcheck.rules.stacking import VALID_SUBSCRIPTS
        
        assert len(VALID_SUBSCRIPTS) == 4
        assert "\u0FB1" in VALID_SUBSCRIPTS  # ya-btags (U+0FB1)
        assert "\u0FB2" in VALID_SUBSCRIPTS  # ra-btags (U+0FB2)
        assert "\u0FB3" in VALID_SUBSCRIPTS  # la-btags (U+0FB3)
        assert "\u0FAD" in VALID_SUBSCRIPTS  # wa-zur (U+0FAD)
    
    def test_ya_btags_valid_combinations(self):
        """ya-btags (U+0FB1) can subscript certain letters"""
        from app.spellcheck.rules.stacking import is_valid_subscript_root
        
        # ya-btags = \u0FB1 (subscript ya) - combines like: ཀྱ (kya)
        # Valid combinations (from VBA line 578)
        assert is_valid_subscript_root("ཀ", "\u0FB1") is True  # ka + ya = ཀྱ (kya)
        assert is_valid_subscript_root("ག", "\u0FB1") is True  # ga + ya = གྱ (gya)
        
        # Invalid combinations (from VBA line 578) 
        assert is_valid_subscript_root("ང", "\u0FB1") is False  # nga + ya invalid
    
    def test_ra_btags_valid_combinations(self):
        """ra-btags (U+0FB2) can subscript certain letters"""
        from app.spellcheck.rules.stacking import is_valid_subscript_root
        
        # ra-btags = \u0FB2 (subscript ra) - combines like: ཀྲ (kra)
        # Valid combinations (from VBA line 608)
        assert is_valid_subscript_root("ཀ", "\u0FB2") is True  # ka + ra = ཀྲ (kra)
        assert is_valid_subscript_root("ག", "\u0FB2") is True  # ga + ra = གྲ (gra)
        
        # Invalid combinations
        assert is_valid_subscript_root("ང", "\u0FB2") is False  # nga + ra invalid
    
    def test_la_btags_valid_combinations(self):
        """la-btags (U+0FB3) can subscript certain letters"""
        from app.spellcheck.rules.stacking import is_valid_subscript_root
        
        # la-btags = \u0FB3 (subscript la) - combines like: ཀླ (kla)
        # Valid combinations (from VBA line 638)
        assert is_valid_subscript_root("ཀ", "\u0FB3") is True  # ka + la = ཀླ (kla)
        assert is_valid_subscript_root("ག", "\u0FB3") is True  # ga + la = གླ (gla)
        
        # Invalid combinations
        assert is_valid_subscript_root("ང", "\u0FB3") is False  # nga + la invalid
    
    def test_wa_zur_valid_combinations(self):
        """wa-zur (U+0FAD) can subscript certain letters"""
        from app.spellcheck.rules.stacking import is_valid_subscript_root
        
        # wa-zur = \u0FAD (subscript wa) - combines like: ཀྭ (kwa)
        # Valid combinations (from VBA line 668)
        assert is_valid_subscript_root("ཀ", "\u0FAD") is True  # ka + wa = ཀྭ (kwa)
        assert is_valid_subscript_root("ག", "\u0FAD") is True  # ga + wa = གྭ (gwa)
        
        # Invalid combinations
        assert is_valid_subscript_root("ང", "\u0FAD") is False  # nga + wa invalid


class TestPrefixRuleBugs_QA_20260211:
    """
    Tests for known bugs in prefix validation data.

    Cross-referencing INVALID_PREFIX_COMBOS against the VBA source
    (Tibetan_Spellchecker_vba.txt line 334) revealed 7 data errors.
    These tests document the correct behavior per the VBA source.

    Bugs found:
    1. ད invalid list has ང — should NOT be there (VBA: 0F44 outside 0F45-0F50)
    2. ད invalid list missing ཏ — should be there (VBA: 0F4F inside 0F45-0F50)
    3. ད invalid list has ལ instead of ཤ — U+0F64 = ཤ, not ལ (U+0F63)
    4. མ invalid list has ལ instead of ཤ — same U+0F64 confusion
    5. 5th prefix key is ར but VBA uses U+0F60 = འ — wrong prefix identity
    6. འ invalid list has ལ instead of ཤ — same U+0F64 confusion
    7. VALID_PREFIXES has 6 entries (includes ར) — should be 5
    """

    # ---- Bug 1: ད + ང should be VALID ----

    def test_da_nga_should_be_valid(self):
        """ད+ང is NOT in VBA's invalid list. དངོས (dngos) is a common word."""
        from app.spellcheck.rules.stacking import is_valid_prefix_root
        assert is_valid_prefix_root("ད", "ང") is True

    # ---- Bug 2: ད + ཏ should be INVALID ----

    def test_da_ta_should_be_invalid(self):
        """ད+ཏ IS in VBA's invalid list (U+0F4F is within 0F45-0F50 range)."""
        from app.spellcheck.rules.stacking import is_valid_prefix_root
        assert is_valid_prefix_root("ད", "ཏ") is False

    # ---- Bug 3: ད has ལ instead of ཤ ----

    def test_da_sha_should_be_invalid(self):
        """ད+ཤ IS in VBA (U+0F64 = ཤ sha). Reference doc mislabeled it as ལ."""
        from app.spellcheck.rules.stacking import is_valid_prefix_root
        assert is_valid_prefix_root("ད", "ཤ") is False

    def test_da_la_should_be_valid(self):
        """ད+ལ is NOT in VBA. ལ (U+0F63) was confused with ཤ (U+0F64)."""
        from app.spellcheck.rules.stacking import is_valid_prefix_root
        assert is_valid_prefix_root("ད", "ལ") is True

    # ---- Bug 4: མ has ལ instead of ཤ ----

    def test_ma_sha_should_be_invalid(self):
        """མ+ཤ IS in VBA (U+0F64 = ཤ). Same mislabeling as ད."""
        from app.spellcheck.rules.stacking import is_valid_prefix_root
        assert is_valid_prefix_root("མ", "ཤ") is False

    def test_ma_la_should_be_valid(self):
        """མ+ལ is NOT in VBA. ལ (U+0F63) was confused with ཤ (U+0F64)."""
        from app.spellcheck.rules.stacking import is_valid_prefix_root
        assert is_valid_prefix_root("མ", "ལ") is True

    # ---- Bugs 5-6: འ prefix keyed as ར, plus ལ/ཤ confusion ----

    def test_achung_ka_should_be_invalid(self):
        """འ+ཀ IS in VBA (U+0F60 = འ is the 5th prefix, not ར)."""
        from app.spellcheck.rules.stacking import is_valid_prefix_root
        assert is_valid_prefix_root("འ", "ཀ") is False

    def test_achung_sha_should_be_invalid(self):
        """འ+ཤ IS in VBA (U+0F64 in འ's invalid list)."""
        from app.spellcheck.rules.stacking import is_valid_prefix_root
        assert is_valid_prefix_root("འ", "ཤ") is False

    def test_achung_ta_should_be_invalid(self):
        """འ+ཏ IS in VBA (U+0F4F in འ's invalid list)."""
        from app.spellcheck.rules.stacking import is_valid_prefix_root
        assert is_valid_prefix_root("འ", "ཏ") is False

    def test_achung_valid_roots(self):
        """འ can prefix these roots (NOT in VBA's invalid list for U+0F60).
        Verified against real words: འགྲོ, འཇིག, འདིར, འབྲས, འཛིན."""
        from app.spellcheck.rules.stacking import is_valid_prefix_root
        assert is_valid_prefix_root("འ", "ག") is True   # འགྲོ ('gro = go)
        assert is_valid_prefix_root("འ", "ཇ") is True   # འཇིག ('jig = destroy)
        assert is_valid_prefix_root("འ", "ད") is True   # འདིར ('dir = here)
        assert is_valid_prefix_root("འ", "བ") is True   # འབྲས ('bras = rice)
        assert is_valid_prefix_root("འ", "ཛ") is True   # འཛིན ('dzin = hold)
        assert is_valid_prefix_root("འ", "ར") is True   # not in invalid list

    def test_achung_invalid_roots(self):
        """འ CANNOT prefix these roots (IN VBA's invalid list for U+0F60)."""
        from app.spellcheck.rules.stacking import is_valid_prefix_root
        assert is_valid_prefix_root("འ", "ཞ") is False  # U+0F5E in VBA invalid
        assert is_valid_prefix_root("འ", "ཟ") is False  # U+0F5F in VBA invalid
        assert is_valid_prefix_root("འ", "ཡ") is False  # U+0F61 in VBA invalid

    # ---- Bug 7: VALID_PREFIXES count ----

    def test_valid_prefixes_should_be_five(self):
        """Traditional grammar has 5 prefixes: ག ད བ མ འ.
        ར (ra, U+0F62) is a superscript, not a prefix.
        The VBA source only defines 5 prefix groups (U+0F42, 0F51, 0F56, 0F58, 0F60).
        """
        from app.spellcheck.rules.stacking import VALID_PREFIXES
        assert "ག" in VALID_PREFIXES
        assert "ད" in VALID_PREFIXES
        assert "བ" in VALID_PREFIXES
        assert "མ" in VALID_PREFIXES
        assert "འ" in VALID_PREFIXES
        assert "ར" not in VALID_PREFIXES  # ra is a superscript, not a prefix
        assert len(VALID_PREFIXES) == 5


class TestRuleHelpers:
    """Test helper/compatibility functions"""
    
    def test_error_severity_mapping(self):
        """Error types map to correct severity"""
        from app.spellcheck.rules import get_error_severity
        
        assert get_error_severity("encoding_error") == "critical"
        assert get_error_severity("invalid_prefix") == "error"
        assert get_error_severity("sanskrit_marker") == "info"
