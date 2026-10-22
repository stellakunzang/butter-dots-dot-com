import type {NextPage} from 'next'
import Link from 'next/link'
import {Layout, Section, Card, SectionHeading} from '../../components'
import {ErrorExample} from '../../components/learn/ErrorExample'
import {LearnHeader} from '../../components/learn/LearnHeader'
import {ParticleTable} from '../../components/learn/ParticleTable'
import {SyllableAnatomy} from '../../components/learn/SyllableAnatomy'
import {SPELL_ERROR_EXAMPLES} from '../../content/learn/errors'
import {
  AGENTIVE_PARTICLES,
  INDEFINITE_PARTICLES,
  LOCATIVE_PARTICLES,
  RELATIONAL_PARTICLES,
} from '../../content/learn/particles'

const SpellingRules: NextPage = () => {
  return (
    <Layout
      title="Tibetan Spelling Rules - Butter Dots"
      description="A guide to classical Tibetan syllable structure and spelling rules"
      showBackLink
      backHref="/learn"
      backLabel="← Learn"
    >
      <LearnHeader
        title="Tibetan Spelling Rules"
        lede="Tibetan syllables follow strict structural rules. This guide explains the components of a syllable and the rules the spellchecker enforces."
      />

      {/* ------------------------------------------------------------------ */}
      {/* Syllable structure                                                   */}
      {/* ------------------------------------------------------------------ */}
      <Section title="Anatomy of a Tibetan Syllable">
        <p className="text-lg mb-6">
          Every Tibetan syllable is built around a single{' '}
          <strong>root letter</strong>. Up to six additional components may
          surround it, each occupying a defined position. Not all positions are
          filled — most syllables use only two or three.
        </p>

        <SyllableAnatomy />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
          <Card title="Prefix (སྔོན་འཇུག)" variant="bordered">
            <p className="mb-3">
              Placed before the root. Only five letters can be prefixes:
            </p>
            <div className="flex gap-4 text-2xl mb-3">
              <span>ག</span>
              <span>ད</span>
              <span>བ</span>
              <span>མ</span>
              <span>འ</span>
            </div>
            <p className="text-sm text-gray-500">
              Not every combination of prefix + root is valid. The spellchecker
              knows which combinations are attested in classical Tibetan.
            </p>
          </Card>

          <Card title="Superscript (མགོ་ཅན)" variant="bordered">
            <p className="mb-3">
              Sits above the root. Only three letters can be superscripts:
            </p>
            <div className="grid grid-cols-3 gap-2 text-sm mb-3">
              <div>
                <span className="text-2xl mr-2">ར</span> ར་མགོ
              </div>
              <div>
                <span className="text-2xl mr-2">ལ</span> ལ་མགོ
              </div>
              <div>
                <span className="text-2xl mr-2">ས</span> ས་མགོ
              </div>
            </div>
            <p className="text-sm text-gray-500">
              Each superscript only combines with specific roots. For example, ས
              can sit above ཀ (སྐ) but not above ར.
            </p>
          </Card>

          <Card title="Subscript (ཞབས་ཀྱུ)" variant="bordered">
            <p className="mb-3">
              Written below the root consonant. Four possible subscripts:
            </p>
            <div className="grid grid-cols-2 gap-2 text-sm mb-3">
              <div>
                <span className="text-2xl mr-2">ྱ</span> ཡ་བཏགས
              </div>
              <div>
                <span className="text-2xl mr-2">ྲ</span> ར་བཏགས
              </div>
              <div>
                <span className="text-2xl mr-2">ླ</span> ལ་བཏགས
              </div>
              <div>
                <span className="text-2xl mr-2">ྭ</span> ཝ་ཟུར
              </div>
            </div>
            <p className="text-sm text-gray-500">
              Like superscripts, each subscript only combines with certain
              roots. For example, ཡ་བཏགས can appear under ཀ (ཀྱ) but not under
              ང.
            </p>
          </Card>

          <Card title="Vowel (དབྱངས)" variant="bordered">
            <p className="mb-3">
              Marked above or below the stack. The default vowel is unmarked ཨ.
            </p>
            <div className="grid grid-cols-2 gap-2 text-sm mb-3">
              <div>
                <span className="text-xl mr-2">ི</span> གི་གུ
              </div>
              <div>
                <span className="text-xl mr-2">ུ</span> ཞབས་ཀྱུ
              </div>
              <div>
                <span className="text-xl mr-2">ེ</span> འགྲེང་བུ
              </div>
              <div>
                <span className="text-xl mr-2">ོ</span> ན་རོ
              </div>
            </div>
            <p className="text-sm text-gray-500">
              Only one vowel mark is allowed per syllable. Two consecutive vowel
              marks is an error, with a few notable exceptions.
            </p>
          </Card>

          <Card title="Suffix (རྗེས་འཇུག)" variant="bordered">
            <p className="mb-3">Follows the root. Ten possible suffixes:</p>
            <div className="flex flex-wrap gap-3 text-2xl mb-3">
              <span>ག</span>
              <span>ང</span>
              <span>ད</span>
              <span>ན</span>
              <span>བ</span>
              <span>མ</span>
              <span>འ</span>
              <span>ར</span>
              <span>ལ</span>
              <span>ས</span>
            </div>
            <p className="text-sm text-gray-500">
              The suffix determines which particle forms are valid after the
              word (see Particle Rules below).
            </p>
          </Card>

          <Card title="Post-suffix (ཡང་འཇུག)" variant="bordered">
            <p className="mb-3">
              The final element, appearing after the suffix. Only two are valid:
            </p>
            <div className="flex gap-4 text-2xl mb-3">
              <span>ད</span>
              <span>ས</span>
            </div>
          </Card>
        </div>

        <div className="mt-6 p-5 bg-blue-50 rounded-lg border border-blue-100">
          <p className="text-sm text-blue-800">
            <strong>Root is required.</strong> Every valid Tibetan syllable must
            have a root consonant. All other components are optional.
          </p>
        </div>
      </Section>

      {/* ------------------------------------------------------------------ */}
      {/* Particle rules                                                       */}
      {/* ------------------------------------------------------------------ */}
      <Section title="Particle Rules">
        <p className="text-lg mb-4">
          Particles are small grammatical words that follow nouns and verbs. In
          classical Tibetan, a particle&apos;s spelling changes depending on the
          last letter of the word it follows. This is called{' '}
          <em>euphonic change</em> — the forms are chosen to make pronunciation
          flow naturally.
        </p>
        <p className="text-lg mb-6">
          The determining factor is the <strong>suffix</strong> of the preceding
          word (or the absence of a suffix).
        </p>
        <p className="mb-8 text-gray-500">
          This section covers which form to write. For what each particle{' '}
          <em>does</em> — and how to use particles to find where words begin and
          end — see{' '}
          <Link
            href="/learn/sentence-structure"
            className="text-gray-700 underline underline-offset-2 hover:text-gray-900"
          >
            Reading a Tibetan Sentence
          </Link>
          .
        </p>

        {/* Relational */}
        <SectionHeading as="h3">
          Relational Particle{' '}
          <span className="text-gray-500 font-light">(འབྲེལ་སྒྲ)</span>
        </SectionHeading>
        <p className="mb-4">
          Marks possession or association (of, &apos;s). The correct form
          depends on the preceding word&apos;s suffix:
        </p>
        <ParticleTable rows={RELATIONAL_PARTICLES} />

        {/* Agentive */}
        <SectionHeading as="h3" className="mt-10">
          Agentive Particle{' '}
          <span className="text-gray-500 font-light">(བྱེད་སྒྲ)</span>
        </SectionHeading>
        <p className="mb-4">
          Marks the agent, instrument, reason, or source of an action — roughly
          equivalent to &ldquo;by,&rdquo; &ldquo;with,&rdquo; or &ldquo;because
          of.&rdquo; The forms follow the same suffix groupings as the
          relational particle:
        </p>
        <ParticleTable rows={AGENTIVE_PARTICLES} />

        {/* Locative */}
        <SectionHeading as="h3" className="mt-10">
          Locative Particle{' '}
          <span className="text-gray-500 font-light">(ལ་དོན)</span>
        </SectionHeading>
        <p className="mb-4">
          Marks location or direction (in, at, to). The ལ་དོན has more forms
          than the other particles. རུ is rare — after འ or no suffix, ར is the
          usual form.
        </p>
        <ParticleTable rows={LOCATIVE_PARTICLES} />

        {/* Indefinite */}
        <SectionHeading as="h3" className="mt-10">
          Indefinite Article{' '}
          <span className="text-gray-500 font-light">(a, one)</span>
        </SectionHeading>
        <p className="mb-4">
          The indefinite article / number one. Three forms based on the
          preceding suffix:
        </p>
        <ParticleTable rows={INDEFINITE_PARTICLES} />
      </Section>

      {/* ------------------------------------------------------------------ */}
      {/* Error types                                                          */}
      {/* ------------------------------------------------------------------ */}
      <Section title="Error Types">
        <p className="text-lg mb-6">
          When the spellchecker finds a problem, it identifies the type of
          error. Here is what each type means:
        </p>

        <div className="space-y-4">
          {SPELL_ERROR_EXAMPLES.map(entry => (
            <ErrorExample key={entry.type} {...entry} />
          ))}
        </div>
      </Section>
    </Layout>
  )
}

export default SpellingRules
