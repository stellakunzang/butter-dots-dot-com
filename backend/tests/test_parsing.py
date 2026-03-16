"""
Tests for Tibetan Syllable Parsing

Tests the parsing stage (parsing/parser.py) through the TibetanSyllableParser
public API. Covers:
- Root identification
- Superscript identification
- Prefix identification
- Complex root identification (multiple components)
- Subscript collection
- Vowel collection
- Suffix collection
- Real-world word parsing
- Parser robustness with invalid input

Previously split across test_component_identifiers.py,
test_component_collectors.py, and test_syllable_parser.py.
"""
from app.spellcheck.syllable_parser import TibetanSyllableParser
from .test_helpers import get_root_base_form, assert_components


# ============================================================================
# CRITICAL REGRESSION TESTS - DO NOT REMOVE
# ============================================================================
# These tests verify specific bugs that were found and fixed.
# If these fail, the parser is broken!

class TestRegressionBugs:
    """
    CRITICAL: These tests protect against known parser bugs.
    
    Bugs discovered 2026-02-11:
    1. སྐད - Superscript was misidentified as root
    2. བརྒྱུད - Subscript was misidentified as root
    
    IF THESE TESTS FAIL, THE PARSER HAS REGRESSED!
    """
    
    def test_regression_skad_superscript(self):
        """REGRESSION: སྐད must identify superscript correctly
        
        Bug: Parser identified ས as root, ྐ as subscript
        Fix: Parser now identifies ས as superscript, ཀ as root
        Date Fixed: 2026-02-11
        """
        parser = TibetanSyllableParser()
        parsed = parser.parse("སྐད")
        
        assert parsed['superscript'] == 'ས', \
            "REGRESSION: ས must be superscript, not root!"
        assert get_root_base_form(parsed) == 'ཀ', \
            "REGRESSION: ཀ must be root, not subscript!"
    
    def test_regression_brgyud_root(self):
        """REGRESSION: བརྒྱུད must identify root correctly
        
        Bug: Parser identified ྱ (subscript) as root
        Fix: Parser now identifies ག as root, ྱ as subscript
        Date Fixed: 2026-02-11
        """
        parser = TibetanSyllableParser()
        parsed = parser.parse("བརྒྱུད")
        
        root = get_root_base_form(parsed)
        assert root == 'ག', \
            f"REGRESSION: Root must be ག, got {root} (was incorrectly ཡ)"
        assert 'ྱ' in parsed['subscripts'], \
            "REGRESSION: ྱ must be subscript, not root!"
    
    def test_regression_spyod_structure(self):
        """REGRESSION: སྤྱོད must parse all components correctly
        
        Date Added: 2026-02-11
        """
        parser = TibetanSyllableParser()
        parsed = parser.parse("སྤྱོད")
        
        assert_components(parsed,
            superscript='ས',
            root='པ',
            has_subscript='ྱ',
            vowel='ོ',
            suffix='ད'
        )


# ============================================================================
# Root Identification
# ============================================================================

class TestRootIdentification:
    """Test root identification in various syllable structures"""
    
    def test_simple_root_with_vowel(self):
        """བོད - Root before vowel"""
        parser = TibetanSyllableParser()
        parsed = parser.parse("བོད")
        
        assert get_root_base_form(parsed) == 'བ'
        assert parsed['vowels'] == ['ོ']
        assert parsed['suffix'] == 'ད'
    
    def test_simple_root_no_vowel(self):
        """དང - Root without vowel mark"""
        parser = TibetanSyllableParser()
        parsed = parser.parse("དང")
        
        assert get_root_base_form(parsed) == 'ད'
        assert parsed['suffix'] == 'ང'
    
    def test_root_with_vowel_only(self):
        """ནི - Root with vowel, no suffix"""
        parser = TibetanSyllableParser()
        parsed = parser.parse("ནི")
        
        assert get_root_base_form(parsed) == 'ན'
        assert parsed['vowels'] == ['ི']
    
    def test_single_consonant_root(self):
        """ལ - Single consonant is root"""
        parser = TibetanSyllableParser()
        parsed = parser.parse("ལ")
        
        assert get_root_base_form(parsed) == 'ལ'
        assert parsed['prefix'] is None
        assert parsed['suffix'] is None


# ============================================================================
# Superscript Identification
# ============================================================================

class TestSuperscriptIdentification:
    """Test superscript detection (above root)"""
    
    def test_sa_mgo_superscript(self):
        """སྐད - sa-mgo superscript"""
        parser = TibetanSyllableParser()
        parsed = parser.parse("སྐད")
        
        assert_components(parsed,
            superscript='ས',
            root='ཀ',
            suffix='ད'
        )
    
    def test_ra_mgo_superscript(self):
        """རྐ - ra-mgo superscript"""
        parser = TibetanSyllableParser()
        parsed = parser.parse("རྐ")
        
        assert parsed['superscript'] == 'ར'
        assert get_root_base_form(parsed) == 'ཀ'
    
    def test_la_mgo_superscript(self):
        """ལྐ - la-mgo superscript"""
        parser = TibetanSyllableParser()
        parsed = parser.parse("ལྐ")
        
        assert parsed['superscript'] == 'ལ'
        assert get_root_base_form(parsed) == 'ཀ'
    
    def test_superscript_with_vowel(self):
        """སྐོ - Superscript + root + vowel"""
        parser = TibetanSyllableParser()
        parsed = parser.parse("སྐོ")
        
        assert_components(parsed,
            superscript='ས',
            root='ཀ',
            vowel='ོ'
        )


# ============================================================================
# Prefix Identification
# ============================================================================

class TestPrefixIdentification:
    """Test prefix detection (before superscript or root)"""
    
    def test_ga_prefix(self):
        """གཉིས - ga prefix"""
        parser = TibetanSyllableParser()
        parsed = parser.parse("གཉིས")
        
        assert_components(parsed,
            prefix='ག',
            root='ཉ'
        )
    
    def test_da_prefix(self):
        """དགོངས - da prefix"""
        parser = TibetanSyllableParser()
        parsed = parser.parse("དགོངས")
        
        assert_components(parsed,
            prefix='ད',
            root='ག'
        )
    
    def test_ba_prefix_with_superscript(self):
        """བསྟན - ba prefix + sa superscript + ta root"""
        parser = TibetanSyllableParser()
        parsed = parser.parse("བསྟན")
        
        assert_components(parsed,
            prefix='བ',
            superscript='ས',
            root='ཏ',
            suffix='ན'
        )
    
    def test_not_prefix_when_invalid(self):
        """པས - pa is NOT a valid prefix
        
        Only 6 valid prefixes: ག ད བ མ འ ར
        So པས = pa(root) + sa(suffix), not prefix+root
        """
        parser = TibetanSyllableParser()
        parsed = parser.parse("པས")
        
        assert parsed['prefix'] is None, "པ is not a valid prefix"
        assert get_root_base_form(parsed) == 'པ'
        assert parsed['suffix'] == 'ས'

    def test_two_letter_prefix_root_when_second_not_valid_suffix(self):
        """གཡ - ག is valid prefix, ཡ is NOT a valid suffix → prefix+root

        Without this fix, _parse_no_vowel required len >= 3 for prefix
        detection, so གཡ was parsed as root=ག, suffix=ཡ. But ཡ is not
        a valid suffix, causing a false positive. Must be prefix+root.
        """
        parser = TibetanSyllableParser()
        parsed = parser.parse("གཡ")

        assert_components(parsed,
            prefix='ག',
            root='ཡ',
        )
        assert parsed['suffix'] is None, \
            "ཡ is not a valid suffix; must be parsed as root"

    def test_two_letter_root_suffix_when_second_is_valid_suffix(self):
        """དང - ང is a valid suffix → root+suffix (existing behavior preserved)

        When both letters could be prefix+root but the second IS a valid
        suffix, the existing root+suffix interpretation should be kept.
        """
        parser = TibetanSyllableParser()
        parsed = parser.parse("དང")

        assert get_root_base_form(parsed) == 'ད'
        assert parsed['suffix'] == 'ང'


# ============================================================================
# Complex Root Identification (multiple components)
# ============================================================================

class TestComplexRootIdentification:
    """Test root identification in complex multi-component syllables"""
    
    def test_prefix_superscript_root_subscript(self):
        """བརྒྱུད - All major components
        
        Structure: བ(prefix) + ར(super) + ྒ(root) + ྱ(sub) + ུ(vowel) + ད(suffix)
        """
        parser = TibetanSyllableParser()
        parsed = parser.parse("བརྒྱུད")
        
        assert_components(parsed,
            prefix='བ',
            superscript='ར',
            root='ག',
            has_subscript='ྱ',
            vowel='ུ',
            suffix='ད'
        )
    
    def test_superscript_root_subscript(self):
        """སྤྱོད - Superscript + root + subscript
        
        Structure: ས(super) + ྤ(root) + ྱ(sub) + ོ(vowel) + ད(suffix)
        """
        parser = TibetanSyllableParser()
        parsed = parser.parse("སྤྱོད")
        
        assert_components(parsed,
            superscript='ས',
            root='པ',
            has_subscript='ྱ',
            vowel='ོ'
        )
    
    def test_prefix_root_subscript(self):
        """འབྲས - Prefix + root + subscript (no superscript)
        
        Structure: འ(prefix) + བ(root) + ྲ(subscript) + ས(suffix)
        """
        parser = TibetanSyllableParser()
        parsed = parser.parse("འབྲས")
        
        assert_components(parsed,
            prefix='འ',
            root='བ',
            has_subscript='ྲ',
            suffix='ས'
        )


# ============================================================================
# Subscript Collection
# ============================================================================

class TestSubscriptCollection:
    """Test subscript identification and collection"""
    
    def test_single_ya_btags(self):
        """བྱ - Single ya-btags subscript"""
        parser = TibetanSyllableParser()
        parsed = parser.parse("བྱ")
        
        assert get_root_base_form(parsed) == 'བ'
        assert 'ྱ' in parsed['subscripts']
        assert len(parsed['subscripts']) == 1
    
    def test_single_ra_btags(self):
        """བྲ - Single ra-btags subscript"""
        parser = TibetanSyllableParser()
        parsed = parser.parse("བྲ")
        
        assert get_root_base_form(parsed) == 'བ'
        assert 'ྲ' in parsed['subscripts']
    
    def test_single_wa_zur(self):
        """ཀྭ - Single wa-zur subscript"""
        parser = TibetanSyllableParser()
        parsed = parser.parse("ཀྭ")
        
        assert get_root_base_form(parsed) == 'ཀ'
        assert '\u0FAD' in parsed['subscripts']
    
    def test_multiple_subscripts(self):
        """གྲྭ - Multiple subscripts on same root
        
        ga root + ra-btags + wa-zur
        """
        parser = TibetanSyllableParser()
        parsed = parser.parse("གྲྭ")
        
        assert get_root_base_form(parsed) == 'ག'
        assert len(parsed['subscripts']) >= 1
        subscript_str = ''.join(parsed['subscripts'])
        assert 'ྲ' in subscript_str or 'ྭ' in subscript_str


# ============================================================================
# Vowel Collection
# ============================================================================

class TestVowelCollection:
    """Test vowel identification and collection"""
    
    def test_single_vowel_i(self):
        """ནི - Single i vowel"""
        parser = TibetanSyllableParser()
        parsed = parser.parse("ནི")
        
        assert parsed['vowels'] == ['ི']
    
    def test_single_vowel_o(self):
        """བོད - Single o vowel"""
        parser = TibetanSyllableParser()
        parsed = parser.parse("བོད")
        
        assert parsed['vowels'] == ['ོ']
    
    def test_single_vowel_u(self):
        """བུ - Single u vowel"""
        parser = TibetanSyllableParser()
        parsed = parser.parse("བུ")
        
        assert parsed['vowels'] == ['ུ']
    
    def test_no_vowel_mark(self):
        """དང - No vowel mark (inherent 'a')"""
        parser = TibetanSyllableParser()
        parsed = parser.parse("དང")
        
        assert parsed['vowels'] == []


# ============================================================================
# Suffix Collection
# ============================================================================

class TestSuffixCollection:
    """Test suffix and post-suffix identification"""
    
    def test_single_suffix(self):
        """བོད - Single suffix"""
        parser = TibetanSyllableParser()
        parsed = parser.parse("བོད")
        
        assert parsed['suffix'] == 'ད'
        assert parsed['post_suffix'] is None
    
    def test_suffix_and_post_suffix_da(self):
        """བོདད - Suffix + da post-suffix"""
        parser = TibetanSyllableParser()
        parsed = parser.parse("བོདད")
        
        assert parsed['suffix'] == 'ད'
        assert parsed['post_suffix'] == 'ད'
    
    def test_suffix_and_post_suffix_sa(self):
        """བོདས - Suffix + sa post-suffix"""
        parser = TibetanSyllableParser()
        parsed = parser.parse("བོདས")
        
        assert parsed['suffix'] == 'ད'
        assert parsed['post_suffix'] == 'ས'
    
    def test_no_suffix(self):
        """ནི - No suffix"""
        parser = TibetanSyllableParser()
        parsed = parser.parse("ནི")
        
        assert parsed['suffix'] is None
        assert parsed['post_suffix'] is None


# ============================================================================
# Parsing Structure Helper
# ============================================================================

class TestParseSyllableStructure:
    """Test parse_syllable_structure (rules compat function)"""
    
    def test_get_syllable_components(self):
        """Parse syllable into components"""
        from app.spellcheck.rules import parse_syllable_structure
        
        # Simple syllable
        simple = "ཀ"
        components = parse_syllable_structure(simple)
        assert components["base"] == "ཀ"
        assert components["prefix"] is None
        
        # With prefix (need 3+ chars for parser to detect prefix in no-vowel case)
        with_prefix = "གཉིས"  # ga(prefix) + nya(root) + i(vowel) + sa(suffix)
        components = parse_syllable_structure(with_prefix)
        assert components["prefix"] == "ག"
        assert components["base"] == "ཉ"
        
        # With subscript
        with_subscript = "ཀྱ"  # kya
        components = parse_syllable_structure(with_subscript)
        assert components["base"] == "ཀ"
        assert components["subscript"] == "ྱ"


# ============================================================================
# Real-World Words
# ============================================================================

class TestRealWorldWords:
    """Integration tests with real Tibetan words
    
    These words MUST parse correctly - they are valid, common words.
    """
    
    def test_bod_yig_tibetan_script(self):
        """བོད་ཡིག - Tibetan script"""
        parser = TibetanSyllableParser()
        
        parsed1 = parser.parse("བོད")
        assert get_root_base_form(parsed1) == 'བ'
        
        parsed2 = parser.parse("ཡིག")
        assert get_root_base_form(parsed2) == 'ཡ'
    
    def test_bod_skad_tibetan_language(self):
        """བོད་སྐད - Tibetan language"""
        parser = TibetanSyllableParser()
        
        parsed = parser.parse("སྐད")
        assert parsed['superscript'] == 'ས'
        assert get_root_base_form(parsed) == 'ཀ'
    
    def test_rgyal_po_king(self):
        """རྒྱལ་པོ - King"""
        parser = TibetanSyllableParser()
        
        parsed = parser.parse("རྒྱལ")
        assert_components(parsed,
            superscript='ར',
            root='ག',
            has_subscript='ྱ'
        )
    
    def test_sangs_rgyas_buddha(self):
        """སངས་རྒྱས - Buddha"""
        parser = TibetanSyllableParser()
        
        parsed1 = parser.parse("སངས")
        assert get_root_base_form(parsed1) == 'ས'
        
        parsed2 = parser.parse("རྒྱས")
        assert parsed2['superscript'] == 'ར'
        assert get_root_base_form(parsed2) == 'ག'


# ============================================================================
# Parser Robustness
# ============================================================================

class TestParserRobustness:
    """Test parser handles invalid structures without crashing
    
    Parser should complete even on invalid input.
    Validation layer catches the errors.
    """
    
    def test_handles_consonants_after_vowel(self):
        """ཨེརྡ - Invalid but parser shouldn't crash"""
        parser = TibetanSyllableParser()
        parsed = parser.parse("ཨེརྡ")
        
        assert parsed is not None
        assert 'root' in parsed
    
    def test_handles_multiple_vowels(self):
        """ཨེཨོ - Invalid but parser shouldn't crash"""
        parser = TibetanSyllableParser()
        parsed = parser.parse("ཨེཨོ")
        
        assert parsed is not None
    
    def test_handles_unusual_marks(self):
        """ཕ༹ཀལ - Unusual structure but parser completes"""
        parser = TibetanSyllableParser()
        parsed = parser.parse("ཕ༹ཀལ")
        
        assert parsed is not None


# ============================================================================
# འི (Achung + I-Vowel) Suffix Parsing
# ============================================================================

class TestAchungISuffixParsing:
    """
    Test correct parsing of འི (achung + i-vowel) as relational suffix.

    In Tibetan, འི can be added to words with no suffix or with suffix འ
    (achung) to form the relational case. This creates a special structure
    where ི appears on the suffix འ, potentially creating a second vowel
    in the syllable.

    CRITICAL: The parser must NOT misidentify འ as the root letter just
    because ི (a vowel) follows it. The root is the main consonant of
    the word; འ here is the suffix.
    """

    # --- Root must NOT be འ when འི is a suffix ---

    def test_ya_achung_i_root_is_ya_not_achung(self):
        """ཡའི (ya'i) - root must be ཡ, NOT འ

        Structure: ཡ (root) + འ (suffix) + ི (suffix vowel)
        The vowel ི follows འ, but འ is the suffix, not the root.
        """
        parser = TibetanSyllableParser()
        parsed = parser.parse("ཡའི")

        assert get_root_base_form(parsed) == 'ཡ', \
            f"Root should be ཡ, got {get_root_base_form(parsed)} -- འ is suffix, not root"
        assert parsed['suffix'] == 'འ'

    def test_pa_achung_i_root_is_pa_not_achung(self):
        """པའི (pa'i) - root must be པ, NOT འ

        Structure: པ (root) + འ (suffix) + ི (suffix vowel)
        Common relational particle.
        """
        parser = TibetanSyllableParser()
        parsed = parser.parse("པའི")

        assert get_root_base_form(parsed) == 'པ', \
            f"Root should be པ, got {get_root_base_form(parsed)}"
        assert parsed['suffix'] == 'འ'

    def test_la_achung_i_root_is_la_not_achung(self):
        """ལའི (la'i) - root must be ལ, NOT འ

        Structure: ལ (root) + འ (suffix) + ི (suffix vowel)
        Common relational form of ལ (postposition/mountain pass).
        """
        parser = TibetanSyllableParser()
        parsed = parser.parse("ལའི")

        assert get_root_base_form(parsed) == 'ལ', \
            f"Root should be ལ, got {get_root_base_form(parsed)}"
        assert parsed['suffix'] == 'འ'

    # --- Prefix + root + འི suffix ---

    def test_dga_i_prefix_da_root_ga(self):
        """དགའི (dga'i) - prefix ད, root ག, suffix འ

        Structure: ད (prefix) + ག (root) + འ (suffix) + ི (suffix vowel)
        Relational of དགའ (dga' = love/joy).
        """
        parser = TibetanSyllableParser()
        parsed = parser.parse("དགའི")

        assert_components(parsed,
            prefix='ད',
            root='ག',
            suffix='འ'
        )

    def test_bka_i_prefix_ba_root_ka(self):
        """བཀའི (bka'i) - prefix བ, root ཀ, suffix འ

        Structure: བ (prefix) + ཀ (root) + འ (suffix) + ི (suffix vowel)
        Relational of བཀའ (bka' = decree/command).
        """
        parser = TibetanSyllableParser()
        parsed = parser.parse("བཀའི")

        assert_components(parsed,
            prefix='བ',
            root='ཀ',
            suffix='འ'
        )

    def test_mkha_i_prefix_ma_root_kha(self):
        """མཁའི (mkha'i) - prefix མ, root ཁ, suffix འ

        Structure: མ (prefix) + ཁ (root) + འ (suffix) + ི (suffix vowel)
        Relational of མཁའ (mkha' = sky/space).
        """
        parser = TibetanSyllableParser()
        parsed = parser.parse("མཁའི")

        assert_components(parsed,
            prefix='མ',
            root='ཁ',
            suffix='འ'
        )

    # --- Root vowel + འི suffix (two vowel marks in syllable) ---

    def test_mtho_i_root_vowel_plus_suffix_vowel(self):
        """མཐོའི (mtho'i) - root has vowel ོ, suffix འ has vowel ི

        Structure: མ (prefix) + ཐ (root) + ོ (root vowel) + འ (suffix) + ི (suffix vowel)
        This syllable legitimately has TWO vowel marks: ོ on root and ི on suffix.
        Relational of མཐོ (mtho = high/tall).
        """
        parser = TibetanSyllableParser()
        parsed = parser.parse("མཐོའི")

        assert_components(parsed,
            prefix='མ',
            root='ཐ',
            vowel='ོ',
            suffix='འ'
        )

    # --- འི should be fully parsed (not left in unparsed) ---

    def test_achung_i_suffix_fully_parsed(self):
        """འི suffix characters should be fully parsed, not left in unparsed"""
        parser = TibetanSyllableParser()

        words_and_roots = [
            ("ཡའི", "ཡ"),
            ("པའི", "པ"),
            ("ལའི", "ལ"),
            ("དགའི", "ག"),
            ("བཀའི", "ཀ"),
        ]

        for word, expected_root in words_and_roots:
            model = parser.parse_to_model(word)
            assert len(model.unparsed) == 0, \
                f"Word {word}: འི suffix should be fully parsed, but unparsed={[tc.char for tc in model.unparsed]}"

    def test_mtho_i_fully_parsed_with_two_vowels(self):
        """མཐོའི - both vowels should be accounted for, nothing unparsed

        This is the hardest case: root vowel ོ AND suffix vowel ི.
        """
        parser = TibetanSyllableParser()
        model = parser.parse_to_model("མཐོའི")

        assert len(model.unparsed) == 0, \
            f"མཐོའི: all characters should be parsed, but unparsed={[tc.char for tc in model.unparsed]}"
