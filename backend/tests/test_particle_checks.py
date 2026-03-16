"""
Tests for particle context validation.

Particles in Tibetan take different forms depending on the suffix of the
preceding word. The spellchecker checks these in check_text (not
check_syllable, since context is required).

Abbreviations used in comments:
  G1 = suffix group {ད བ ས}  → ཀྱི / ཀྱིས / ཅིག
  G2 = suffix group {ག ང}    → གི  / གིས
  G3 = suffix group {ན མ ར ལ} → གྱི / གྱིས
  G4 = suffix འ or no suffix  → འི  / ས   / ར  / རུ
"""
import pytest
from app.spellcheck.engine import TibetanSpellChecker


@pytest.fixture
def engine():
    return TibetanSpellChecker()


def particle_errors(engine, text):
    """Return only wrong_particle_form errors from check_text."""
    return [
        e for e in engine.check_text(text)
        if e.get('error_type') == 'wrong_particle_form'
    ]


def no_particle_errors(engine, text):
    return particle_errors(engine, text) == []


# ============================================================================
# Relational particle (bdag gi sgra)
# ============================================================================

class TestRelationalParticle:

    def test_kyi_after_da_suffix_valid(self, engine):
        """བོད་ཀྱི་ — ད suffix → ཀྱི correct"""
        assert no_particle_errors(engine, "བོད་ཀྱི་")

    def test_kyi_after_ba_suffix_valid(self, engine):
        """དེབ་ཀྱི་ — བ suffix → ཀྱི correct"""
        assert no_particle_errors(engine, "དེབ་ཀྱི་")

    def test_gi_after_nga_suffix_valid(self, engine):
        """ཤིང་གི་ — ང suffix → གི correct"""
        assert no_particle_errors(engine, "ཤིང་གི་")

    def test_gyi_after_la_suffix_valid(self, engine):
        """ཡུལ་གྱི་ — ལ suffix → གྱི correct"""
        assert no_particle_errors(engine, "ཡུལ་གྱི་")

    def test_gyi_after_na_suffix_valid(self, engine):
        """རྒྱུན་གྱི་ — ན suffix → གྱི correct"""
        assert no_particle_errors(engine, "རྒྱུན་གྱི་")

    def test_yi_after_no_suffix_valid(self, engine):
        """ཁྱི་འི་ — no suffix → འི correct"""
        assert no_particle_errors(engine, "ཁྱི་འི་")

    def test_yi_lenient_valid_after_any_suffix(self, engine):
        """བོད་ཡི་ — ཡི is lenient variant, always valid"""
        assert no_particle_errors(engine, "བོད་ཡི་")

    def test_kyi_after_nga_suffix_invalid(self, engine):
        """ཤིང་ཀྱི་ — ང suffix needs གི, not ཀྱི"""
        errors = particle_errors(engine, "ཤིང་ཀྱི་")
        assert len(errors) == 1
        assert errors[0]['word'] == 'ཀྱི'
        assert 'གི' in errors[0]['message']

    def test_gi_after_da_suffix_invalid(self, engine):
        """བོད་གི་ — ད suffix needs ཀྱི, not གི"""
        errors = particle_errors(engine, "བོད་གི་")
        assert len(errors) == 1
        assert errors[0]['word'] == 'གི'

    def test_gyi_after_nga_suffix_invalid(self, engine):
        """ཤིང་གྱི་ — ང suffix needs གི, not གྱི"""
        errors = particle_errors(engine, "ཤིང་གྱི་")
        assert len(errors) == 1
        assert errors[0]['word'] == 'གྱི'

    def test_yi_after_da_suffix_valid_lenient(self, engine):
        """བོད་ཡི་ — ད suffix would need ཀྱི, but ཡི is always accepted"""
        assert no_particle_errors(engine, "བོད་ཡི་")


# ============================================================================
# Agentive particle (byed pa'i sgra)
# ============================================================================

class TestAgentiveParticle:

    def test_kyis_after_da_suffix_valid(self, engine):
        """བོད་ཀྱིས་ — ད suffix → ཀྱིས correct"""
        assert no_particle_errors(engine, "བོད་ཀྱིས་")

    def test_gis_after_nga_suffix_valid(self, engine):
        """ཤིང་གིས་ — ང suffix → གིས correct"""
        assert no_particle_errors(engine, "ཤིང་གིས་")

    def test_gyis_after_la_suffix_valid(self, engine):
        """ཡུལ་གྱིས་ — ལ suffix → གྱིས correct"""
        assert no_particle_errors(engine, "ཡུལ་གྱིས་")

    def test_sa_after_no_suffix_valid(self, engine):
        """ཁྱི་ས་ — no suffix → ས correct"""
        assert no_particle_errors(engine, "ཁྱི་ས་")

    def test_yis_lenient_always_valid(self, engine):
        """བོད་ཡིས་ — ཡིས is lenient variant, always valid"""
        assert no_particle_errors(engine, "བོད་ཡིས་")

    def test_gis_after_da_suffix_invalid(self, engine):
        """བོད་གིས་ — ད suffix needs ཀྱིས, not གིས"""
        errors = particle_errors(engine, "བོད་གིས་")
        assert len(errors) == 1
        assert errors[0]['word'] == 'གིས'

    def test_kyis_after_nga_suffix_invalid(self, engine):
        """ཤིང་ཀྱིས་ — ང suffix needs གིས, not ཀྱིས"""
        errors = particle_errors(engine, "ཤིང་ཀྱིས་")
        assert len(errors) == 1
        assert errors[0]['word'] == 'ཀྱིས'


# ============================================================================
# Locative particle (gnas gzhi'i sgra)
# ============================================================================

class TestLocativeParticle:

    def test_na_unrestricted(self, engine):
        """ན is valid after any suffix"""
        for text in ["བོད་ན་", "ཤིང་ན་", "ཡུལ་ན་", "ཁྱི་ན་"]:
            assert no_particle_errors(engine, text), f"ན should be valid in {text}"

    def test_la_unrestricted(self, engine):
        """ལ is valid after any suffix"""
        for text in ["བོད་ལ་", "ཤིང་ལ་", "ཡུལ་ལ་", "ཁྱི་ལ་"]:
            assert no_particle_errors(engine, text), f"ལ should be valid in {text}"

    def test_su_after_sa_suffix_valid(self, engine):
        """ཤེས་སུ་ — ས suffix → སུ correct"""
        assert no_particle_errors(engine, "ཤེས་སུ་")

    def test_su_after_da_suffix_invalid(self, engine):
        """བོད་སུ་ — ད suffix: སུ is not valid here"""
        errors = particle_errors(engine, "བོད་སུ་")
        assert len(errors) == 1
        assert errors[0]['word'] == 'སུ'

    def test_du_after_la_suffix_valid(self, engine):
        """ཡུལ་དུ་ — ལ suffix → དུ correct"""
        assert no_particle_errors(engine, "ཡུལ་དུ་")

    def test_du_after_nga_suffix_valid(self, engine):
        """ཤིང་དུ་ — ང suffix → དུ correct"""
        assert no_particle_errors(engine, "ཤིང་དུ་")

    def test_tu_after_ga_suffix_valid(self, engine):
        """ཕྱག་ཏུ་ — ག suffix → ཏུ correct"""
        assert no_particle_errors(engine, "ཕྱག་ཏུ་")

    def test_tu_after_la_suffix_invalid(self, engine):
        """ཡུལ་ཏུ་ — ལ suffix needs དུ, not ཏུ"""
        errors = particle_errors(engine, "ཡུལ་ཏུ་")
        assert len(errors) == 1
        assert errors[0]['word'] == 'ཏུ'


# ============================================================================
# Indefinite article (sgra med kyi sgra)
# ============================================================================

class TestIndefiniteArticle:

    def test_cig_after_da_suffix_valid(self, engine):
        """བོད་ཅིག་ — ད suffix → ཅིག correct"""
        assert no_particle_errors(engine, "བོད་ཅིག་")

    def test_cig_after_ba_suffix_valid(self, engine):
        """དེབ་ཅིག་ — བ suffix → ཅིག correct"""
        assert no_particle_errors(engine, "དེབ་ཅིག་")

    def test_shig_after_sa_suffix_valid(self, engine):
        """ཤེས་ཤིག་ — ས suffix → ཤིག correct"""
        assert no_particle_errors(engine, "ཤེས་ཤིག་")

    def test_zhig_after_nga_suffix_valid(self, engine):
        """ཤིང་ཞིག་ — ང suffix → ཞིག correct"""
        assert no_particle_errors(engine, "ཤིང་ཞིག་")

    def test_zhig_after_la_suffix_valid(self, engine):
        """ཡུལ་ཞིག་ — ལ suffix → ཞིག correct"""
        assert no_particle_errors(engine, "ཡུལ་ཞིག་")

    def test_zhig_after_no_suffix_valid(self, engine):
        """ཁྱི་ཞིག་ — no suffix → ཞིག correct"""
        assert no_particle_errors(engine, "ཁྱི་ཞིག་")

    def test_zhig_after_da_suffix_invalid(self, engine):
        """བོད་ཞིག་ — ད suffix needs ཅིག, not ཞིག"""
        errors = particle_errors(engine, "བོད་ཞིག་")
        assert len(errors) == 1
        assert errors[0]['word'] == 'ཞིག'
        assert 'ཅིག' in errors[0]['message']

    def test_zhig_after_sa_suffix_invalid(self, engine):
        """ཤེས་ཞིག་ — ས suffix needs ཤིག, not ཞིག"""
        errors = particle_errors(engine, "ཤེས་ཞིག་")
        assert len(errors) == 1
        assert errors[0]['word'] == 'ཞིག'

    def test_cig_after_nga_suffix_invalid(self, engine):
        """ཤིང་ཅིག་ — ང suffix needs ཞིག, not ཅིག"""
        errors = particle_errors(engine, "ཤིང་ཅིག་")
        assert len(errors) == 1
        assert errors[0]['word'] == 'ཅིག'


# ============================================================================
# Edge cases
# ============================================================================

class TestParticleEdgeCases:

    def test_particle_after_structurally_invalid_syllable_not_double_flagged(self, engine):
        """
        If the preceding syllable is already invalid, don't also flag the particle.
        Avoids noise: one error is enough.
        """
        # གཀར is invalid (ga cannot prefix ka); following ཀྱི should not be flagged
        errors = engine.check_text("གཀར་ཀྱི་")
        particle_errs = [e for e in errors if e.get('error_type') == 'wrong_particle_form']
        assert len(particle_errs) == 0, (
            "Particle after an already-invalid syllable should not be flagged"
        )

    def test_particle_at_start_of_text_not_flagged(self, engine):
        """
        A particle at the very start of text (no preceding syllable) should not crash.
        """
        errors = engine.check_text("ཀྱི་བོད་")
        # No wrong_particle_form errors (there's no preceding syllable to check)
        particle_errs = [e for e in errors if e.get('error_type') == 'wrong_particle_form']
        assert len(particle_errs) == 0

    def test_multiple_particles_in_text(self, engine):
        """Several particles in one text: each is checked against its own predecessor."""
        # བོད་ཀྱི་ is valid; ཤིང་གི་ is valid
        errors = engine.check_text("བོད་ཀྱི་ཤིང་གི་")
        particle_errs = [e for e in errors if e.get('error_type') == 'wrong_particle_form']
        assert len(particle_errs) == 0

    def test_wrong_particle_error_has_required_fields(self, engine):
        """Wrong particle error dict has all required fields."""
        errors = particle_errors(engine, "བོད་གི་")
        assert len(errors) == 1
        err = errors[0]
        assert 'word' in err
        assert 'position' in err
        assert 'error_type' in err
        assert 'severity' in err
        assert 'message' in err
        assert err['severity'] == 'error'
