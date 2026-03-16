import type {NextPage} from 'next'
import {Layout, Section, Card} from '../components'

const SpellingRules: NextPage = () => {
  return (
    <Layout
      title="Tibetan Spelling Rules - Butter Dots"
      description="A guide to classical Tibetan syllable structure and spelling rules"
      showBackLink
    >
      <div className="mb-12 max-w-4xl mx-auto border-b-2 border-gray-200 pb-8">
        <div className="mb-4">
          <span className="text-sm uppercase tracking-wider text-gray-500 font-medium">
            Reference Guide
          </span>
        </div>
        <h1 className="text-5xl md:text-6xl font-serif text-gray-900 mb-4 tracking-tight">
          Tibetan Spelling Rules
        </h1>
        <p className="text-xl text-gray-600 font-light leading-relaxed">
          Tibetan syllables follow strict structural rules. This guide explains
          the components of a syllable and the rules the spellchecker enforces.
        </p>
      </div>

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

        {/* Visual diagram */}
        <div className="my-8 p-6 bg-gray-50 rounded-xl border border-gray-200 overflow-x-auto">
          <table className="w-full text-center border-collapse">
            <thead>
              <tr>
                <th className="px-4 py-2 text-xs uppercase tracking-wider text-gray-400 font-medium border-b border-gray-200">
                  Prefix
                </th>
                <th className="px-4 py-2 text-xs uppercase tracking-wider text-gray-400 font-medium border-b border-gray-200">
                  Superscript
                </th>
                <th className="px-4 py-2 text-xs uppercase tracking-wider text-gray-400 font-medium border-b border-gray-200 bg-yellow-50">
                  Root
                </th>
                <th className="px-4 py-2 text-xs uppercase tracking-wider text-gray-400 font-medium border-b border-gray-200">
                  Subscript
                </th>
                <th className="px-4 py-2 text-xs uppercase tracking-wider text-gray-400 font-medium border-b border-gray-200">
                  Vowel
                </th>
                <th className="px-4 py-2 text-xs uppercase tracking-wider text-gray-400 font-medium border-b border-gray-200">
                  Suffix
                </th>
                <th className="px-4 py-2 text-xs uppercase tracking-wider text-gray-400 font-medium border-b border-gray-200">
                  Post-suffix
                </th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="px-4 py-3 text-gray-500 text-sm">before root</td>
                <td className="px-4 py-3 text-gray-500 text-sm">above root</td>
                <td className="px-4 py-3 text-gray-900 font-semibold text-sm bg-yellow-50">
                  root letter
                </td>
                <td className="px-4 py-3 text-gray-500 text-sm">below root</td>
                <td className="px-4 py-3 text-gray-500 text-sm">
                  above or below stack
                </td>
                <td className="px-4 py-3 text-gray-500 text-sm">after root</td>
                <td className="px-4 py-3 text-gray-500 text-sm">final</td>
              </tr>
              <tr className="border-t border-gray-100">
                <td className="px-4 py-3 text-2xl text-gray-700">བ</td>
                <td className="px-4 py-3 text-2xl text-gray-700">ས</td>
                <td className="px-4 py-3 text-3xl font-semibold text-gray-900 bg-yellow-50">
                  ག
                </td>
                <td className="px-4 py-3 text-gray-400 text-sm">ྲ</td>
                <td className="px-4 py-3 text-gray-400 text-sm">—</td>
                <td className="px-4 py-3 text-2xl text-gray-700">བ</td>
                <td className="px-4 py-3 text-gray-400 text-sm">—</td>
              </tr>
              <tr className="border-t border-gray-100">
                <td colSpan={7} className="px-4 py-3 text-center">
                  <span className="text-2xl text-gray-900 mr-4">བསྒྲུབ</span>
                  <span className="text-gray-500 text-sm">
                    (<em>bsgrub</em> — to accomplish)
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

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
            <div className="flex gap-4 text-2xl mb-3">
              <span title="ra-mgo">ར</span>
              <span title="la-mgo">ལ</span>
              <span title="sa-mgo">ས</span>
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
            <div className="flex gap-4 items-end mb-3">
              <span className="text-2xl" title="ya-btags">
                ྱ
              </span>
              <span className="text-2xl" title="ra-btags">
                ྲ
              </span>
              <span className="text-2xl" title="la-btags">
                ླ
              </span>
              <span className="text-2xl" title="wa-zur">
                ྭ
              </span>
            </div>
            <p className="text-sm text-gray-500">
              Like superscripts, each subscript only combines with certain
              roots. For example, ya-btags (ྱ) can appear under ཀ (ཀྱ) but not
              under ང.
            </p>
          </Card>

          <Card title="Vowel" variant="bordered">
            <p className="mb-3">
              Marked above the stack. The default vowel is <em>a</em>{' '}
              (unmarked).
            </p>
            <div className="grid grid-cols-2 gap-2 text-sm mb-3">
              <div>
                <span className="text-xl mr-2">ི</span> <em>gigu</em>
              </div>
              <div>
                <span className="text-xl mr-2">ུ</span> <em>shabkyu</em>
              </div>
              <div>
                <span className="text-xl mr-2">ེ</span> <em>drangbu</em>
              </div>
              <div>
                <span className="text-xl mr-2">ོ</span> <em>naro</em>
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

        {/* Relational */}
        <h3 className="text-2xl font-serif text-gray-900 mt-8 mb-4">
          Relational Particle{' '}
          <span className="text-gray-500 font-light">(of, &apos;s)</span>
        </h3>
        <p className="mb-4">
          Marks possession or association. The correct form depends on the
          preceding word&apos;s suffix:
        </p>
        <ParticleTable
          rows={[
            {
              particle: 'ཀྱི',
              suffixes: 'ད  བ  ས',
              example: 'བོད་ཀྱི་',
              exampleGloss: 'of Tibet',
            },
            {
              particle: 'གི',
              suffixes: 'ག  ང',
              example: 'ཆོས་གི་',
              exampleGloss: 'of the dharma',
            },
            {
              particle: 'གྱི',
              suffixes: 'ན  མ  ར  ལ',
              example: 'སེམས་ཅན་གྱི་',
              exampleGloss: 'of beings',
            },
            {
              particle: 'འི',
              suffixes: 'འ  or no suffix',
              example: 'ལྷའི་',
              exampleGloss: 'of the deity',
            },
            {
              particle: 'ཡི',
              suffixes: 'any (lenient variant)',
              example: 'ལྷ་ཡི་',
              exampleGloss: 'used in poetry for metrical reasons',
              lenient: true,
            },
          ]}
        />

        {/* Agentive */}
        <h3 className="text-2xl font-serif text-gray-900 mt-10 mb-4">
          Agentive Particle{' '}
          <span className="text-gray-500 font-light">(by, with)</span>
        </h3>
        <p className="mb-4">
          Marks the agent, instrument, reason, or source of an action — roughly
          equivalent to &ldquo;by,&rdquo; &ldquo;with,&rdquo; or &ldquo;because
          of.&rdquo; The forms follow the same suffix groupings as the
          relational particle:
        </p>
        <ParticleTable
          rows={[
            {
              particle: 'ཀྱིས',
              suffixes: 'ད  བ  ས',
              example: 'བོད་ཀྱིས་',
              exampleGloss: 'by Tibet',
            },
            {
              particle: 'གིས',
              suffixes: 'ག  ང',
              example: 'ཆོས་གིས་',
              exampleGloss: 'by the dharma',
            },
            {
              particle: 'གྱིས',
              suffixes: 'ན  མ  ར  ལ',
              example: 'སེམས་ཅན་གྱིས་',
              exampleGloss: 'by beings',
            },
            {
              particle: 'ས',
              suffixes: 'འ  or no suffix',
              example: 'ལྷས་',
              exampleGloss: 'by the deity',
            },
            {
              particle: 'ཡིས',
              suffixes: 'any (lenient variant)',
              example: '',
              exampleGloss: 'used in poetry for metrical reasons',
              lenient: true,
            },
          ]}
        />

        {/* Locative */}
        <h3 className="text-2xl font-serif text-gray-900 mt-10 mb-4">
          Locative Particle{' '}
          <span className="text-gray-500 font-light">(in, at, to)</span>
        </h3>
        <p className="mb-4">
          Marks location or direction. The locative has more forms than the
          other particles:
        </p>
        <ParticleTable
          rows={[
            {
              particle: 'ན',
              suffixes: 'any suffix or no suffix',
              example: 'བོད་ན་',
              exampleGloss: 'in Tibet',
            },
            {
              particle: 'ལ',
              suffixes: 'any suffix or no suffix',
              example: 'བོད་ལ་',
              exampleGloss: 'to Tibet',
            },
            {
              particle: 'སུ',
              suffixes: 'ས',
              example: 'ཆོས་སུ་',
              exampleGloss: 'into the dharma',
            },
            {
              particle: 'ཏུ',
              suffixes: 'ག  བ  (or post-suffix ད)',
              example: 'ཕྱོགས་ཏུ་',
              exampleGloss: 'in the direction',
            },
            {
              particle: 'དུ',
              suffixes: 'ང  ད  ན  མ  ར  ལ',
              example: 'བར་དུ་',
              exampleGloss: 'until',
            },
            {
              particle: 'རུ',
              suffixes: 'འ  or no suffix',
              example: 'རྒྱལ་ཁབ་རུ་',
              exampleGloss: 'in the kingdom',
            },
            {
              particle: 'ར',
              suffixes: 'འ',
              example: 'ཆེར་',
              exampleGloss: 'greatly',
            },
          ]}
        />

        {/* Indefinite */}
        <h3 className="text-2xl font-serif text-gray-900 mt-10 mb-4">
          Indefinite Article{' '}
          <span className="text-gray-500 font-light">(a, one)</span>
        </h3>
        <p className="mb-4">
          The indefinite article / number one. Three forms based on the
          preceding suffix:
        </p>
        <ParticleTable
          rows={[
            {
              particle: 'ཅིག',
              suffixes: 'ག  ད  བ',
              example: 'ཆོས་ཅིག་',
              exampleGloss: 'a dharma',
            },
            {
              particle: 'ཤིག',
              suffixes: 'ས',
              example: 'ཕྱོགས་ཤིག་',
              exampleGloss: 'a direction',
            },
            {
              particle: 'ཞིག',
              suffixes: 'ང  ན  མ  ར  ལ  འ  or no suffix',
              example: 'ལྷ་ཞིག་',
              exampleGloss: 'a deity',
            },
          ]}
        />
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
          <ErrorEntry
            type="Wrong particle form"
            example="བོད་གི་"
            description="The particle doesn't match the suffix of the word before it. Here གི་ is used after བོད་ (which ends in ད), but ད calls for ཀྱི་."
            fix="Use ཀྱི་ after words ending in ད, བ, or ས."
          />
          <ErrorEntry
            type="Invalid prefix combination"
            example="ཧཧིབ་"
            description="The letter before the root is not a valid prefix for that root. ཧ (ha) cannot act as a prefix."
            fix="Only the five prefix letters (ག ད བ མ འ) can precede a root, and only in attested combinations."
          />
          <ErrorEntry
            type="Invalid superscript combination"
            example=""
            description="A superscript letter is stacked above a root it cannot combine with. Each of the three superscripts (ར ལ ས) only stacks above specific roots — for example, ས can sit above ཀ to form སྐ, but not above ར."
            fix="Check which roots are valid for that superscript."
          />
          <ErrorEntry
            type="Invalid subscript combination"
            example="ངྱི"
            description="The subscript below the root is not valid for that root. ང (nga) cannot take a ya-btags subscript."
            fix="Subscripts (ྱ ྲ ླ ྭ) only combine with certain roots."
          />
          <ErrorEntry
            type="Invalid suffix"
            example="ཀཝ་"
            description="The letter after the root is not one of the ten valid suffixes."
            fix="Only these ten letters can be suffixes: ག ང ད ན བ མ འ ར ལ ས."
          />
          <ErrorEntry
            type="Double vowel"
            example=""
            description="Two vowel marks appear on the same syllable, which is structurally impossible."
            fix="Each syllable can only carry one vowel mark."
          />
          <ErrorEntry
            type="Encoding error (critical)"
            example="wrong character"
            description="A character that looks like Tibetan is actually the wrong Unicode codepoint — a common issue when text is copied from certain older fonts or systems."
            fix="Re-type the syllable from scratch using a Unicode Tibetan keyboard, or use a font conversion tool."
          />
        </div>
      </Section>
    </Layout>
  )
}

// -------------------------------------------------------------------------
// Sub-components
// -------------------------------------------------------------------------

interface ParticleRow {
  particle: string
  suffixes: string
  example: string
  exampleGloss: string
  lenient?: boolean
}

function ParticleTable({rows}: {rows: ParticleRow[]}) {
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 mb-2">
      <table className="w-full text-sm border-collapse">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-gray-500 font-medium border-b border-gray-200 w-24">
              Particle
            </th>
            <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-gray-500 font-medium border-b border-gray-200">
              Used after suffix
            </th>
            <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-gray-500 font-medium border-b border-gray-200">
              Example
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={row.particle}
              className={[
                i < rows.length - 1 ? 'border-b border-gray-100' : '',
                row.lenient ? 'bg-gray-50' : 'bg-white',
              ].join(' ')}
            >
              <td className="px-4 py-3">
                <span className="text-2xl text-gray-900">{row.particle}</span>
                {row.lenient && (
                  <span className="ml-2 text-xs text-gray-400 align-middle">
                    lenient
                  </span>
                )}
              </td>
              <td className="px-4 py-3 text-gray-600 font-mono tracking-wide">
                {row.suffixes}
              </td>
              <td className="px-4 py-3">
                {row.example && (
                  <>
                    <span className="text-xl text-gray-900 mr-2">
                      {row.example}
                    </span>
                    <span className="text-gray-400 italic">
                      {row.exampleGloss}
                    </span>
                  </>
                )}
                {!row.example && (
                  <span className="text-gray-400 italic">
                    {row.exampleGloss}
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

interface ErrorEntryProps {
  type: string
  example: string
  description: string
  fix: string
}

function ErrorEntry({type, example, description, fix}: ErrorEntryProps) {
  return (
    <div className="p-5 bg-white rounded-lg border border-gray-200">
      <div className="flex items-start gap-4 flex-wrap">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-2 flex-wrap">
            <h4 className="text-base font-semibold text-gray-900 m-0">
              {type}
            </h4>
            <span className="text-lg text-red-600 font-medium">{example}</span>
          </div>
          <p className="text-sm text-gray-600 mb-2">{description}</p>
          <p className="text-sm text-gray-500">
            <span className="font-medium text-gray-700">Fix: </span>
            {fix}
          </p>
        </div>
      </div>
    </div>
  )
}

export default SpellingRules
