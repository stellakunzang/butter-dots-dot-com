import type {NextPage} from 'next'
import Link from 'next/link'
import {
  Layout,
  Section,
  Card,
  PageTitle,
  SectionHeading,
  Button,
} from '../../components'

const TIB = {
  bod: '\u0F56\u0F7C\u0F51',
  tashiDelek:
    '\u0F56\u0F40\u0FB2\u0F0B\u0F64\u0F72\u0F66\u0F0B\u0F56\u0F51\u0F7A\u0F0B\u0F63\u0F7A\u0F42\u0F66',
  tsek: '\u0F0B',
  tsekName: '\u0F5A\u0F7A\u0F42',
  ka: '\u0F40',
  bkra: '\u0F56\u0F40\u0FB2',
  she: '\u0F0D',
  sheName: '\u0F64\u0F51',
  achung: '\u0F60',
}

const WylieExample = ({wylie, tibetan}: {wylie: string; tibetan: string}) => (
  <div className="flex items-center gap-3 my-3 flex-wrap">
    <code className="bg-gray-100 px-2 py-1 rounded font-mono text-sm text-pink-600 border border-gray-200">
      {wylie}
    </code>
    <span className="text-gray-400 font-bold text-xl">{'\u2192'}</span>
    <span
      className="text-3xl text-gray-900 leading-relaxed"
      style={{fontFamily: 'Jomolhari, serif'}}
    >
      {tibetan}
    </span>
  </div>
)

const TypingTibetan: NextPage = () => {
  return (
    <Layout
      title="How to Type Tibetan - Butter Dots"
      description="A simple guide to Wylie, Tibetan keyboards, and fonts on Mac, Windows, and mobile devices"
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
        <PageTitle>How to Type Tibetan</PageTitle>
        <p className="text-xl text-gray-600 font-light leading-relaxed">
          You can type Tibetan with the keyboard you already have. This page
          explains the system for doing that, how to turn it on, and how to
          install the font this community uses for practice texts.
        </p>
      </div>

      <Section title="What Is Wylie?">
        <p className="text-lg mb-4">
          Wylie is a way of writing Tibetan with ordinary English letters. Each
          Tibetan letter has a matching Latin letter (or a short pair of
          letters). You type those, and your computer turns them into Tibetan
          script.
        </p>
        <p className="text-lg mb-6">
          It is named after Turrell Wylie, who published the system in 1959 so
          that scholars could write Tibetan on a typewriter. It is still the
          most common way to type Tibetan on a computer.
        </p>

        <div className="my-8 p-6 bg-gray-50 rounded-xl border border-gray-200">
          <WylieExample wylie="bod" tibetan={TIB.bod} />
          <WylieExample wylie="bkra shis bde legs" tibetan={TIB.tashiDelek} />
        </div>

        <p className="text-lg mb-4">
          Treat Wylie with caution. It follows the <em>spelling</em>, not the
          sound. If you read Wylie out loud as if it were English, you will not
          be speaking Tibetan.
        </p>
        <p className="text-lg">
          So{' '}
          <code className="bg-gray-100 px-1.5 py-0.5 rounded font-mono text-sm">
            bod
          </code>{' '}
          is how {TIB.bod} is spelled. Many people say it more like
          &ldquo;pö.&rdquo; It is a way to type the written form, not a guide to
          pronunciation.
        </p>
      </Section>

      <Section title="Turn It On — Mac">
        <p className="text-lg mb-6">
          A Mac already includes a Wylie keyboard. You only need to switch it
          on.
        </p>
        <ol className="list-decimal pl-6 space-y-3 text-lg">
          <li>
            Open <strong>System Settings</strong> (on older Macs this is called
            System Preferences).
          </li>
          <li>
            Go to <strong>Keyboard</strong>, then <strong>Input Sources</strong>
            . You may need to click <strong>Edit</strong> first.
          </li>
          <li>
            Click the <strong>+</strong> button.
          </li>
          <li>
            Scroll to <strong>Tibetan</strong> and choose{' '}
            <strong>Tibetan — Wylie</strong>. (Tibetan — EWTS is a close cousin.
            Either will work for everyday typing.)
          </li>
          <li>
            Click <strong>Add</strong>.
          </li>
        </ol>
        <p className="text-lg mt-6">
          To switch keyboards, click the icon in the menu bar at the top of the
          screen — it often looks like a flag or a character — and choose
          Tibetan. On many Macs the Globe key (next to the space bar) also
          switches. When you want English again, switch back the same way.
        </p>
      </Section>

      <Section title="Turn It On — Windows">
        <p className="text-lg mb-4">
          Windows can type Tibetan, but the keyboard it includes is not Wylie.
          It is a Tibetan-script layout, with letters in different places from
          an English keyboard. That is fine if you already know it. For Wylie,
          the usual path is a free program called Keyman.
        </p>

        <SectionHeading as="h3" className="mt-6">
          If you want Wylie
        </SectionHeading>
        <ol className="list-decimal pl-6 space-y-3 text-lg">
          <li>
            Go to{' '}
            <a
              href="https://keyman.com/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-700 underline underline-offset-2 hover:text-gray-900"
            >
              keyman.com
            </a>{' '}
            and install Keyman.
          </li>
          <li>
            In Keyman, add a Tibetan keyboard. Search for <strong>EWTS</strong>{' '}
            or <strong>Wylie</strong> — Extended Wylie (EWTS) is the one most
            people use.
          </li>
          <li>
            Switch to it with <strong>Windows + Space</strong>, or click the
            language icon on the taskbar.
          </li>
        </ol>

        <SectionHeading as="h3">
          If you only need Tibetan letters
        </SectionHeading>
        <ol className="list-decimal pl-6 space-y-3 text-lg">
          <li>
            Open <strong>Settings</strong> →{' '}
            <strong>Time &amp; language</strong> →{' '}
            <strong>Language &amp; region</strong>.
          </li>
          <li>
            Click <strong>Add a language</strong>, search for{' '}
            <strong>Tibetan</strong>, and install it.
          </li>
          <li>
            Switch with <strong>Windows + Space</strong>.
          </li>
        </ol>
      </Section>

      <Section title="On a Phone">
        <p className="text-lg mb-4">
          Phones usually do not use Wylie. They give you a Tibetan keyboard, and
          you tap the letters themselves. That is the easier path on a small
          screen.
        </p>

        <Card title="iPhone or iPad" variant="bordered">
          <ol className="list-decimal pl-6 space-y-2">
            <li>
              Open <strong>Settings</strong> → <strong>General</strong> →{' '}
              <strong>Keyboard</strong> → <strong>Keyboards</strong>.
            </li>
            <li>
              Tap <strong>Add New Keyboard…</strong> and choose{' '}
              <strong>Tibetan</strong>.
            </li>
            <li>
              When you are typing, tap the Globe key to switch to Tibetan.
            </li>
          </ol>
        </Card>

        <Card title="Android" variant="bordered">
          <ol className="list-decimal pl-6 space-y-2">
            <li>
              Open the Gboard settings (or your keyboard settings). The path is
              often <strong>Settings</strong> → <strong>System</strong> →{' '}
              <strong>Languages &amp; input</strong>.
            </li>
            <li>
              Add a language and choose <strong>Tibetan</strong>.
            </li>
            <li>When you are typing, tap the Globe key to switch.</li>
          </ol>
        </Card>

        <p className="text-lg mt-4">
          On an iPhone, stacks do not form by themselves — you tap a stack
          symbol between the letters. The next section covers that. If you
          specifically want Wylie on a phone, Keyman also makes an iOS and
          Android app. Most people prefer the built-in Tibetan keyboard.
        </p>
      </Section>

      <Section title="A Few Things to Note">
        <p className="text-lg mb-6">
          Once the Wylie keyboard is on, these are the habits that matter most:
        </p>
        <ul className="list-disc pl-6 space-y-3 text-lg">
          <li>
            Type a space for the {TIB.tsekName} ({TIB.tsek}), the mark between
            syllables.
          </li>
          <li>
            The vowel <em>a</em> is already there — you do not type it.{' '}
            <code className="bg-gray-100 px-1.5 py-0.5 rounded font-mono text-sm">
              ka
            </code>{' '}
            and{' '}
            <code className="bg-gray-100 px-1.5 py-0.5 rounded font-mono text-sm">
              k
            </code>{' '}
            both make {TIB.ka}. Type{' '}
            <code className="bg-gray-100 px-1.5 py-0.5 rounded font-mono text-sm">
              i
            </code>
            ,{' '}
            <code className="bg-gray-100 px-1.5 py-0.5 rounded font-mono text-sm">
              u
            </code>
            ,{' '}
            <code className="bg-gray-100 px-1.5 py-0.5 rounded font-mono text-sm">
              e
            </code>
            , or{' '}
            <code className="bg-gray-100 px-1.5 py-0.5 rounded font-mono text-sm">
              o
            </code>{' '}
            after the letter for the other vowels.
          </li>
          <li>
            On a computer, stacked letters are typed in order, left to right as
            they are spelled:{' '}
            <code className="bg-gray-100 px-1.5 py-0.5 rounded font-mono text-sm">
              bkra
            </code>{' '}
            becomes {TIB.bkra}. The keyboard builds the stack for you when the
            combination is a normal Tibetan one.
          </li>
          <li>A single apostrophe is a {TIB.achung}.</li>
          <li>
            Type{' '}
            <code className="bg-gray-100 px-1.5 py-0.5 rounded font-mono text-sm">
              /
            </code>{' '}
            for a {TIB.sheName} ({TIB.she}).
          </li>
        </ul>
      </Section>

      <Section title="How Stacks Work">
        <p className="text-lg mb-4">
          On a computer, ordinary stacks take care of themselves. Type the
          letters in spelling order — prefix, superscript, root, subscript — and
          the keyboard builds the stack when the combination is a normal Tibetan
          one.
        </p>

        <SectionHeading as="h3">On a phone</SectionHeading>
        <p className="text-lg mb-6">
          On an iPhone the Tibetan keyboard does not stack automatically. You
          type a letter, then tap the stack key — the one with a downward arrow
          — then the next letter. Repeat the stack key for each letter that
          should join the stack. (Android keyboards vary; some stack on their
          own, some use a similar key.)
        </p>

        <SectionHeading as="h3">Sanskrit and unusual stacks</SectionHeading>
        <p className="text-lg mb-4">
          Standard Tibetan stacks follow the usual spelling rules, and the
          keyboard handles them. Sanskritized Tibetan and other non-standard
          stacks use extra conventions. This is the reference we use for those:
        </p>
        <p className="text-lg">
          <a
            href="https://thlib.org/terms/#/texts/67579/67591"
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-700 underline underline-offset-2 hover:text-gray-900"
          >
            THL Extended Wylie
          </a>
          {' — '}
          Tibetan and Himalayan Library
        </p>
      </Section>

      <Section title="Install Jomolhari">
        <p className="text-lg mb-4">
          A keyboard puts Tibetan <em>letters</em> on the screen. A{' '}
          <strong>font</strong> is what makes those letters look like Tibetan
          handwriting — the right shapes, the stacks sitting in the right place.
        </p>
        <p className="text-lg mb-6">
          The font this community uses for practice texts is{' '}
          <strong>Jomolhari</strong>. This site uses it too. If you install it
          on your computer and choose it in your document, what you type will
          match what other people are looking at.
        </p>

        <div className="mb-8">
          <Button
            href="https://fonts.google.com/specimen/Jomolhari"
            variant="primary"
            target="_blank"
            rel="noopener noreferrer"
          >
            Download Jomolhari from Google Fonts
          </Button>
        </div>
        <p className="text-gray-500 mb-8">
          On that page, click <strong>Get font</strong> and then{' '}
          <strong>Download all</strong>. You will get a zip file. Open it and
          find the{' '}
          <code className="bg-gray-100 px-1.5 py-0.5 rounded font-mono text-sm">
            .ttf
          </code>{' '}
          file inside.
        </p>

        <Card title="On a Mac" variant="bordered">
          <ol className="list-decimal pl-6 space-y-2">
            <li>Double-click the Jomolhari font file.</li>
            <li>
              Font Book opens. Click <strong>Install</strong>.
            </li>
            <li>
              The font is now available in Pages, Word, and most other apps. You
              may need to quit and reopen an app that was already open.
            </li>
          </ol>
        </Card>

        <Card title="On Windows" variant="bordered">
          <ol className="list-decimal pl-6 space-y-2">
            <li>Right-click the Jomolhari font file.</li>
            <li>
              Choose <strong>Install</strong> (or{' '}
              <strong>Install for all users</strong> if you see that).
            </li>
            <li>
              Close and reopen Word or your browser so they can see the new
              font.
            </li>
          </ol>
        </Card>
      </Section>

      <Section
        title="Why the Same Text Looks Different in Each App"
        variant="highlight"
      >
        <p className="text-lg mb-4">
          This can be the source of frustration and why we usually share PDFs.
          Google Docs, Microsoft Word, and Apple Pages each come with a
          different default Tibetan font:
        </p>
        <ul className="list-disc pl-6 space-y-2 text-lg mb-6">
          <li>
            <strong>Pages</strong> (Mac) usually uses <strong>Kailasa</strong>,
            Apple&apos;s built-in Tibetan font.
          </li>
          <li>
            <strong>Word</strong> on Windows usually uses{' '}
            <strong>Microsoft Himalaya</strong>.
          </li>
          <li>
            <strong>Google Docs</strong> usually uses{' '}
            <strong>Noto Sans Tibetan</strong>.
          </li>
        </ul>
        <p className="text-lg mb-4">
          The letters underneath are the same. The drawing on top is not. Stacks
          and vowel marks can sit differently. A file that looks clean in Pages
          can look cramped or slightly wrong in Word, and the other way around.
        </p>
        <p className="text-lg mb-4">
          Sharing makes it worse. Word and Pages do not pack the font into the
          file. If the other person does not have Jomolhari installed, their
          computer silently picks a substitute, and the page no longer matches
          what you saw.
        </p>
        <p className="text-lg mb-4">
          Microsoft Himalaya has a further problem: when Word exports a PDF, the
          Tibetan often cannot be copied out as real text. It looks fine on the
          page and comes out as garbage when you paste it. That is why a scanned
          or Himalaya PDF sometimes has to go through{' '}
          <Link
            href="/spellcheck"
            className="text-gray-700 underline underline-offset-2 hover:text-gray-900"
          >
            the spell checker&apos;s PDF path
          </Link>{' '}
          instead of a simple copy and paste.
        </p>
        <p className="text-lg">
          The practical habit: install Jomolhari, then{' '}
          <em>set the font yourself</em> in the document — do not leave it on
          the app&apos;s default. Anyone you share with will need Jomolhari too,
          or the file will drift the next time it is opened.
        </p>
      </Section>

      <Section title="What's Next" variant="minimal">
        <p className="text-lg">
          Once you can type a syllable,{' '}
          <Link
            href="/learn/spelling-rules"
            className="text-gray-700 underline underline-offset-2 hover:text-gray-900"
          >
            Spelling Rules
          </Link>{' '}
          shows how those letters stack, and{' '}
          <Link
            href="/learn/sentence-structure"
            className="text-gray-700 underline underline-offset-2 hover:text-gray-900"
          >
            Reading a Tibetan Sentence
          </Link>{' '}
          shows how particles help you find the words.
        </p>
      </Section>
    </Layout>
  )
}

export default TypingTibetan
