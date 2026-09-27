import type {NextPage} from 'next'
import Link from 'next/link'
import {
  Layout,
  Section,
  Card,
  PageTitle,
  SectionHeading,
} from '../../components'

const EXAMPLE_SENTENCE =
  'མ་ནམ་མཁའ་དང་མཉམ་པའི་སེམས་ཅན་ཐམས་ཅད་བདེ་བ་དང་བདེ་བའི་རྒྱུ་དང་ལྡན་པར་གྱུར་ཅིག།'

const EXAMPLE_SYLLABLES = EXAMPLE_SENTENCE.replace(/[།\s]/g, '')
  .split('་')
  .filter(Boolean)

const EXAMPLE_WORDS: {tibetan: string; gloss: string}[] = [
  {tibetan: 'མ', gloss: 'mother'},
  {tibetan: 'ནམ་མཁའ', gloss: 'space'},
  {tibetan: 'དང', gloss: 'and'},
  {tibetan: 'མཉམ་པའི', gloss: 'equal'},
  {tibetan: 'སེམས་ཅན', gloss: 'sentient beings'},
  {tibetan: 'ཐམས་ཅད', gloss: 'all'},
  {tibetan: 'བདེ་བ', gloss: 'happiness'},
  {tibetan: 'དང', gloss: 'and'},
  {tibetan: 'བདེ་བའི', gloss: 'of happiness'},
  {tibetan: 'རྒྱུ', gloss: 'cause'},
  {tibetan: 'དང', gloss: 'and'},
  {tibetan: 'ལྡན་པར', gloss: 'endowed with'},
  {tibetan: 'གྱུར་ཅིག', gloss: 'may they become'},
]

const SentenceStructure: NextPage = () => {
  return (
    <Layout
      title="Reading a Tibetan Sentence - Butter Dots"
      description="How to break down a Tibetan sentence: finding the particles, understanding what they do, and seeing where words begin and end"
      showBackLink
      backHref="/learn"
      backLabel="← Learn"
    >
      <div className="mb-12 max-w-4xl mx-auto border-b-2 border-gray-200 pb-8">
        <div className="mb-4">
          <span className="text-sm uppercase tracking-wider text-gray-500 font-medium">
            Learn
          </span>
        </div>
        <PageTitle>Reading a Tibetan Sentence</PageTitle>
        <p className="text-xl text-gray-600 font-light leading-relaxed">
          The Tibetan language marks syllables, not words. To read a sentence
          you have to work out for yourself where each word begins and ends —
          and the particles are your best clue. This guide explains what the
          particles do and how to use them to take a sentence apart.
        </p>
        <p className="mt-4 text-gray-500">
          For the spelling of each particle — which form is correct after which
          letter — see{' '}
          <Link
            href="/learn/spelling-rules"
            className="text-gray-700 underline underline-offset-2 hover:text-gray-900"
          >
            Spelling Rules
          </Link>
          . This page is about what the particles mean.
        </p>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Where words begin and end                                            */}
      {/* ------------------------------------------------------------------ */}
      <Section title="Why There Are No Word Boundaries">
        <p className="text-lg mb-4">
          English separates every word with a space, so the eye gets the
          boundaries for free. Tibetan separates every <em>syllable</em> with a
          ཚེག (་). A ཚེག is not a space. It tells you a syllable has ended, and
          says nothing at all about whether the word has ended with it.
        </p>
        <p className="text-lg mb-6">
          A word may be one syllable or several. Nothing in the writing marks
          the difference. The reader supplies it.
        </p>

        <div className="my-8 p-6 bg-gray-50 rounded-xl border border-gray-200 space-y-6">
          <BreakdownRow label="What is written">
            <span className="text-2xl text-gray-900 leading-relaxed">
              {EXAMPLE_SENTENCE}
            </span>
          </BreakdownRow>

          <BreakdownRow label="In English">
            <span className="text-gray-700 italic">
              May all sentient beings{' '}
              <span className="underline decoration-dotted decoration-gray-400 underline-offset-4">
                who have been my
              </span>{' '}
              mother,{' '}
              <span className="underline decoration-dotted decoration-gray-400 underline-offset-4">
                as limitless
              </span>{' '}
              as space, enjoy happiness and the causes of happiness.
            </span>
            <p className="text-sm text-gray-500 mt-3 mb-0 leading-relaxed">
              The dotted words are not on the page. The Tibetan says མ — mother
              — and མཉམ — equal. A reader who knows the four immeasurables fills
              in the rest.
            </p>
          </BreakdownRow>

          <BreakdownRow label="Twenty-one syllables, divided by ཚེག (་)">
            <div className="flex flex-wrap gap-2">
              {EXAMPLE_SYLLABLES.map((syllable, i) => (
                <span
                  key={i}
                  className="px-3 py-1 text-2xl text-gray-700 bg-white rounded border border-gray-200"
                >
                  {syllable}
                </span>
              ))}
            </div>
          </BreakdownRow>

          <BreakdownRow label="But only thirteen words">
            <div className="flex flex-wrap gap-3">
              {EXAMPLE_WORDS.map((word, i) => (
                <WordChip key={i} tibetan={word.tibetan} gloss={word.gloss} />
              ))}
            </div>
          </BreakdownRow>

          <BreakdownRow label="The འི that is not a word">
            <p className="text-gray-700 mb-4 leading-relaxed">
              Twice, a{' '}
              <a
                href="#relational"
                className="text-gray-700 underline underline-offset-2 hover:text-gray-900"
              >
                relational
              </a>{' '}
              འི particle is written onto the end of a syllable. It does not get
              its own ཚེག, so it never appears as a syllable of its own, and it
              is not counted among the thirteen words. What it adds is a
              relationship, not a definition.
            </p>
            <div className="flex flex-wrap gap-3">
              <WordChip
                tibetan="མཉམ་པའི་སེམས་ཅན"
                gloss="sentient beings who are equal"
              />
              <WordChip tibetan="བདེ་བའི་རྒྱུ" gloss="the cause of happiness" />
            </div>
          </BreakdownRow>
        </div>

        <p className="text-lg mb-4">
          Most of these words are two syllables; a few are one. Knowing that དང
          is a particle is what lets you place the boundaries around it — it
          cannot be part of the word before it or the word after it, so each དང
          splits the string.
        </p>
        <p className="text-lg mb-4">
          The three དངs are easy to spot because they stand alone. The two འིs
          do the same kind of grammatical work from inside a syllable — པའི, བའི
          — which is why they are easier to miss. This is the contracted form of
          the relational particle below, used when the syllable it attaches to
          has no suffix of its own.
        </p>
        <p className="text-lg mb-4">
          The English above is the translation our community uses. It is longer
          than the Tibetan because it has to be. Tibetan favors the concise
          statement, and in verse especially it will omit what a native speaker
          already knows. English has no such compact; the understanding has to
          be written out in words that were never there.
        </p>
      </Section>

      {/* ------------------------------------------------------------------ */}
      {/* Punctuation                                                          */}
      {/* ------------------------------------------------------------------ */}
      <Section title="The Marks That Divide Text">
        <p className="text-lg mb-6">
          Before looking at particles, it helps to know the punctuation. These
          marks give you the coarse divisions — where a clause stops, where a
          passage begins — and you make those cuts first.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card title="ཚེག" variant="bordered">
            <div className="text-4xl text-gray-900 mb-3">་</div>
            <p className="mb-3">
              Ends a syllable. The single most common mark on the page, and the
              one most often misread as a word break.
            </p>
            <p className="text-sm text-gray-500">
              Treat it as neutral. It divides syllables and tells you nothing
              about words.
            </p>
          </Card>

          <Card title="ཤད" variant="bordered">
            <div className="text-4xl text-gray-900 mb-3">།</div>
            <p className="mb-3">
              Ends a clause or a sentence. Closest to a full stop, though it is
              also used where English would use a comma or a line break in
              verse.
            </p>
            <p className="text-sm text-gray-500">
              A real boundary. Whatever comes before it is a complete unit.
            </p>
          </Card>

          <Card title="ཉིས་ཤད" variant="bordered">
            <div className="text-4xl text-gray-900 mb-3">།།</div>
            <p className="mb-3">
              Closes a larger unit — the end of a section, a chapter, or a
              verse.
            </p>
            <p className="text-sm text-gray-500">
              A stronger version of the same signal.
            </p>
          </Card>

          <Card title="ཡིག་མགོ" variant="bordered">
            <div className="text-4xl text-gray-900 mb-3">༄༅</div>
            <p className="mb-3">
              The head mark. Opens a text or a page. It is decorative rather
              than grammatical.
            </p>
            <p className="text-sm text-gray-500">
              Not part of the sentence — skip past it.
            </p>
          </Card>
        </div>

        <div className="mt-6 p-5 bg-blue-50 rounded-lg border border-blue-100">
          <p className="text-sm text-blue-800">
            <strong>The ཚེག (་) before a ཤད (།).</strong> Normally the ཚེག is
            dropped immediately before a ཤད. The exception is a syllable ending
            in ང, which keeps its ཚེག (ང་།). If you see a ཚེག hugging a ཤད, look
            at the letter in front of it.
          </p>
        </div>
      </Section>

      {/* ------------------------------------------------------------------ */}
      {/* Particles                                                            */}
      {/* ------------------------------------------------------------------ */}
      <Section title="Particles: The Seams of a Sentence">
        <p className="text-lg mb-4">
          A particle is a small syllable with no meaning of its own that
          attaches to a word and does a grammatical job — marking who did
          something, tying two nouns together, or closing off a clause. They are
          the seams of the sentence, and finding them is most of the work of
          reading one.
        </p>
        <p className="text-lg mb-6">
          Grammar books disagree about what to call these categories. Below,
          each one is given the plain name used on this site, followed by the
          other names you are likely to meet elsewhere and the Tibetan name
          where there is a standard one.
        </p>

        <SectionHeading as="h3">
          Particles that mark a word&apos;s role
        </SectionHeading>
        <p className="mb-6">
          These attach to a noun and say what that noun is doing in the sentence
          — who acted, what belongs to what, where something is. Collectively
          they are often called <em>case particles</em>.
        </p>

        <div className="space-y-4">
          <ParticleCategory
            id="relational"
            name="Relational"
            meaning="of, 's"
            alsoCalled="genitive, possessive, connective case"
            tibetanName="འབྲེལ་སྒྲ"
            forms={['ཀྱི', 'གི', 'གྱི', 'འི', 'ཡི']}
            role="Ties two nouns into a single phrase, the way 'of' does in English. The first noun modifies the second."
            example={{
              text: 'བོད་ཀྱི་སྐད་ཡིག',
              gloss: 'the language of Tibet or Tibetan language',
            }}
          />

          <ParticleCategory
            name="Agentive"
            meaning="by, with"
            alsoCalled="instrumental, ergative, agentive case"
            tibetanName="བྱེད་སྒྲ"
            forms={['ཀྱིས', 'གིས', 'གྱིས', 'ས', 'ཡིས']}
            role="Marks the one who performs the action, or the instrument used to perform it. Where English relies on word order to show who did what, Tibetan marks it."
            example={{text: 'ལྷས', gloss: 'by the deity'}}
          />

          <ParticleCategory
            name="Locative"
            meaning="to, in, at, for"
            alsoCalled="dative-locative, la-don, oblique"
            tibetanName="ལ་དོན"
            forms={['ལ', 'ན', 'སུ', 'ཏུ', 'དུ', 'རུ', 'ར']}
            role="Places the noun in space, time, or purpose. This is the broadest of the case particles and its English translation shifts a great deal with context."
            example={{text: 'བོད་ལ', gloss: 'to Tibet or in Tibet'}}
          />

          <ParticleCategory
            name="Source"
            meaning="from, out of"
            alsoCalled="ablative, elative"
            tibetanName="འབྱུང་ཁུངས"
            forms={['ནས', 'ལས']}
            role="Marks where something comes from, or the point it starts from. ནས also does duty as a clause linker meaning 'having done', so check whether it follows a noun or a verb."
            example={{text: 'བོད་ནས', gloss: 'from Tibet'}}
          />

          <ParticleCategory
            name="Comparative"
            meaning="than"
            alsoCalled="ablative of comparison"
            forms={['ལས', 'བས', 'པས']}
            role="Sets up a comparison. Shares its forms with the source particle, so the two are told apart by what surrounds them."
          />
        </div>

        <SectionHeading as="h3" className="mt-12">
          Particles that join or end clauses
        </SectionHeading>
        <p className="mb-6">
          These operate on whole clauses rather than single words. They are the
          strongest boundary signals on the page after the punctuation itself.
        </p>

        <div className="space-y-4">
          <ParticleCategory
            name="And"
            meaning="and, or, with"
            alsoCalled="coordinating particle, comitative"
            forms={['དང']}
            role="Joins nouns into a list. It can also mean 'or', or 'together with'. Unlike English 'and', it is usually repeated after every item rather than only the last."
          />

          <ParticleCategory
            name="Continuative"
            meaning="and, while"
            alsoCalled="gerundive, conjunctive particle"
            forms={['ཅིང', 'ཞིང', 'ཤིང']}
            role="Links two clauses of roughly equal weight, like the '-ing' in 'sitting down, he spoke'. The clause before it is finished; the sentence is not."
          />

          <ParticleCategory
            name="Sequential"
            meaning="having done, and then, so"
            alsoCalled="semi-final particle, connective"
            forms={['ཏེ', 'སྟེ', 'དེ']}
            role="Ends a clause and hands off to the next one, often with a sense of 'having done this, then that'. One of the clearest places to cut a long sentence."
          />

          <ParticleCategory
            name="Conditional"
            meaning="if, when"
            alsoCalled="conditional particle"
            forms={['ན']}
            role="Makes the clause before it a condition. Identical in spelling to the locative ན, and told apart by whether it follows a verb or a noun."
          />

          <ParticleCategory
            name="Also"
            meaning="also, even, although"
            alsoCalled="concessive, adversative"
            forms={['ཀྱང', 'ཡང', 'འང']}
            role="Usually just 'also' or 'too'. After a verb it can mean 'even' or 'although'."
          />

          <ParticleCategory
            name="Topic marker"
            meaning="as for, regarding"
            alsoCalled="topicalizer, isolating particle"
            forms={['ནི']}
            role="Lifts out the thing the sentence is about and sets it aside before the rest follows. It marks emphasis or contrast rather than grammatical role, and it is not translated into English as often as it appears."
            example={{text: 'བོད་ཡིག་ནི', gloss: 'as for Tibetan writing…'}}
          />

          <ParticleCategory
            name="Final"
            meaning="(closes a statement)"
            alsoCalled="terminative, final particle, closing particle"
            forms={['འོ', 'གོ', 'ངོ', 'དོ', 'ནོ', 'བོ', 'མོ', 'རོ', 'སོ', 'ཏོ']}
            role="Declares the sentence over. It carries no translatable meaning; it is punctuation made of letters, and normally sits just before a ཤད (།). The spelling is based on the last letter of the preceding syllable."
          />
        </div>

        <SectionHeading as="h3" className="mt-12">
          Particles that change or extend a word
        </SectionHeading>
        <p className="mb-6">
          These do not divide anything. They fasten onto a word and stay part of
          the phrase, which is exactly why they cause trouble when you go
          looking for the word in a dictionary.
        </p>

        <div className="space-y-4">
          <ParticleCategory
            name="Nominalizer"
            meaning="the act of doing, the one who does"
            alsoCalled="gerund, substantive particle, nominalizing particle"
            forms={['པ', 'བ']}
            role="Turns a verb into a noun. English often uses a gerund for the same job — 'suffering' in 'samsara is suffering'. It is also what makes many ordinary nouns and adjectives, so it is extremely common. In the example below འཁོར is a verb but འཁོར་བ is a noun."
            example={{
              text: 'འཁོར་བ་ནི་སྡུག་བསྔལ།',
              gloss: 'samsara is suffering',
            }}
          />

          <ParticleCategory
            name="Plural"
            meaning="(more than one)"
            alsoCalled="plural marker"
            forms={['རྣམས', 'ཚོ', 'དག']}
            role="Marks a noun as plural. Optional in Tibetan — a bare noun is not necessarily singular, so its absence proves nothing."
          />

          <ParticleCategory
            name="Indefinite"
            meaning="a, one, a certain"
            alsoCalled="indefinite article, indefinite particle"
            forms={['ཅིག', 'ཤིག', 'ཞིག']}
            role="Marks the noun as one unspecified instance, like English 'a'."
          />
        </div>

        <div className="mt-8 p-5 bg-blue-50 rounded-lg border border-blue-100">
          <p className="text-sm text-blue-800">
            <strong>Why one particle has several spellings.</strong> Most of the
            forms listed above are the same particle written differently
            depending on the last letter of the word in front of it. Which form
            is correct where is covered in{' '}
            <Link
              href="/learn/spelling-rules"
              className="underline underline-offset-2 hover:text-blue-900"
            >
              Spelling Rules
            </Link>
            .
          </p>
        </div>
      </Section>

      {/* ------------------------------------------------------------------ */}
      {/* Negatives                                                            */}
      {/* ------------------------------------------------------------------ */}
      <Section title="Negatives">
        <p className="text-lg mb-4">
          A negative flips the sentence. Miss one and the translation comes out
          backwards. They are small, they sit in front of what they negate, and
          མ in particular is easy to mistake for something else.
        </p>
        <p className="text-lg mb-6">
          མི and མ are particles. མིན and མེད are verbs that do the same job —
          the &quot;is not&quot; and &quot;there is not&quot; of Tibetan. All
          four are worth hunting for before you settle on a reading.
        </p>

        <div className="space-y-4">
          <ParticleCategory
            name="Not"
            meaning="not, don't"
            alsoCalled="negative particle, verbal negation"
            tibetanName="དགག་སྒྲ"
            forms={['མི', 'མ']}
            role="Sits in front of a verb and flips it. མི is the usual form with present and future; མ is common with past, and it is also the 'don't' of a command (མ་བྱེད). A negative མ comes before a verb. If it comes before a noun, it is something else."
            example={{text: 'མི་འདོད', gloss: 'does not want'}}
          />

          <ParticleCategory
            name="Is not"
            meaning="isn't"
            alsoCalled="negative copula"
            forms={['མིན']}
            role="The negative of ཡིན. Use it when the sentence would otherwise say that something is something."
            example={{text: 'ཆོས་མིན', gloss: 'it is not the dharma'}}
          />

          <ParticleCategory
            name="Without"
            meaning="there is not"
            alsoCalled="negative existential"
            forms={['མེད']}
            role="The negative of ཡོད. After a noun it often means 'without' rather than a full 'there is no'."
            example={{
              text: 'འཇིགས་མེད',
              gloss: 'there is no fear; fearless',
            }}
          />
        </div>

        <div className="mt-8 p-5 bg-yellow-50 rounded-xl border border-yellow-200/60">
          <p className="text-sm text-gray-800 mb-3">
            <strong>The མ in the opening sentence is not a negative.</strong>{' '}
            མ་ནམ་མཁའ་དང་མཉམ་པའི་སེམས་ཅན is &quot;mother sentient beings equal to
            space.&quot; That first མ means mother. A negative མ would sit in
            front of a verb; this one sits in front of ནམ་མཁའ, a noun.
          </p>
        </div>
      </Section>

      {/* ------------------------------------------------------------------ */}
      {/* Connect or divide                                                    */}
      {/* ------------------------------------------------------------------ */}
      <Section title="Connect or Divide">
        <p className="text-lg mb-4">
          Every particle does one of two things to the text around it. It either
          binds what it touches into a larger unit, or it closes a unit off.
          Deciding which is happening is what turns a string of syllables into a
          sentence you can read.
        </p>

        <div className="my-8 p-6 bg-yellow-50 rounded-xl border border-yellow-200/60">
          <p className="text-lg text-gray-800 m-0">
            <strong>Particles look backward.</strong> A particle attaches to the
            word before it, not the word after it. So when you spot one, you
            have found the <em>end</em> of something. Read backwards from the
            particle to find the phrase it governs.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card title="Particles that connect" variant="bordered">
            <p className="mb-4">
              These pull two things into one. The phrase continues through them.
            </p>
            <ul className="space-y-3 text-sm">
              <BehaviourItem
                particle="ཀྱི"
                note="binds two nouns into one noun phrase"
              />
              <BehaviourItem particle="དང" note="strings nouns into a list" />
              <BehaviourItem
                particle="པ"
                note="fuses to the verb and becomes part of the word"
              />
              <BehaviourItem
                particle="རྣམས"
                note="stays attached to the noun it counts"
              />
            </ul>
          </Card>

          <Card title="Particles that divide" variant="bordered">
            <p className="mb-4">
              These close something off. Cut the sentence here.
            </p>
            <ul className="space-y-3 text-sm">
              <BehaviourItem
                particle="སྟེ"
                note="ends the clause and hands off to the next"
              />
              <BehaviourItem
                particle="ཅིང"
                note="ends the clause, joins it to a matching one"
              />
              <BehaviourItem
                particle="ནི"
                note="sets the topic apart from the rest"
              />
              <BehaviourItem particle="འོ" note="ends the sentence" />
            </ul>
          </Card>
        </div>

        <p className="text-lg mt-8">
          The case particles sit in between. A relational ཀྱི connects the noun
          in front of it to the noun behind it, but it also marks the right edge
          of the first noun — it connects the phrase and divides the words at
          the same time. That double duty is what makes them so useful for
          finding boundaries.
        </p>
      </Section>
    </Layout>
  )
}

// -------------------------------------------------------------------------
// Sub-components
// -------------------------------------------------------------------------

function BreakdownRow({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wider text-gray-400 font-medium mb-2">
        {label}
      </div>
      {children}
    </div>
  )
}

function WordChip({tibetan, gloss}: {tibetan: string; gloss: string}) {
  return (
    <span className="px-4 py-2 bg-white rounded-lg border border-gray-300">
      <span className="text-2xl text-gray-900 mr-2">{tibetan}</span>
      <span className="text-sm text-gray-500 italic">{gloss}</span>
    </span>
  )
}

interface ParticleCategoryProps {
  id?: string
  name: string
  meaning: string
  alsoCalled: string
  tibetanName?: string
  forms: string[]
  role: string
  example?: {text: string; gloss: string}
}

function ParticleCategory({
  id,
  name,
  meaning,
  alsoCalled,
  tibetanName,
  forms,
  role,
  example,
}: ParticleCategoryProps) {
  return (
    <div
      id={id}
      className="p-5 bg-white rounded-lg border border-gray-200 scroll-mt-28"
    >
      <div className="flex items-baseline gap-3 flex-wrap mb-1">
        <h4 className="text-base font-semibold text-gray-900 m-0">{name}</h4>
        <span className="text-gray-500">{meaning}</span>
        {tibetanName && (
          <span className="text-lg text-gray-700">{tibetanName}</span>
        )}
      </div>
      <p className="text-xs text-gray-400 mb-4">
        Elsewhere called: {alsoCalled}
      </p>

      <div className="flex flex-wrap gap-2 mb-4">
        {forms.map(form => (
          <span
            key={form}
            className="px-3 py-1 text-xl text-gray-900 bg-gray-50 rounded border border-gray-200"
          >
            {form}
          </span>
        ))}
      </div>

      <p className="text-sm text-gray-600 mb-0">{role}</p>

      {example && (
        <p className="text-sm mt-3 mb-0">
          <span className="text-xl text-gray-900 mr-2">{example.text}</span>
          <span className="text-gray-400 italic">{example.gloss}</span>
        </p>
      )}
    </div>
  )
}

function BehaviourItem({particle, note}: {particle: string; note: string}) {
  return (
    <li className="flex items-baseline gap-3">
      <span className="text-xl text-gray-900 w-10 shrink-0">{particle}</span>
      <span className="text-gray-600">{note}</span>
    </li>
  )
}

export default SentenceStructure
