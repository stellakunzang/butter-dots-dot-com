import type {NextPage} from 'next'
import {Layout, Section, Button, Card, CodeBlock, PageTitle, SectionHeading} from '../components'

const Resources: NextPage = () => {
  return (
    <Layout
      title="Tibetan Resources - Butter Dots"
      description="Resources for installing Tibetan fonts and keyboards"
      showBackLink
    >
      <div className="mb-12 max-w-4xl mx-auto border-b-2 border-gray-200 pb-8">
        <div className="mb-4">
          <span className="text-sm uppercase tracking-wider text-gray-500 font-medium">
            Language Tools & Resources
          </span>
        </div>
        <PageTitle>Tibetan Language Resources</PageTitle>
        <p className="text-xl text-gray-600 font-light leading-relaxed">
          A comprehensive collection of fonts, keyboard layouts, and tools for working with the Tibetan script and language.
        </p>
      </div>

      <Section title="Quick Install (macOS)" variant="highlight">
        <div className="space-y-6">
          <p className="text-lg">Download and run our automated installer script:</p>
          <div className="flex gap-4 items-center">
            <Button
              href="/install-tibetan-fonts.sh"
              download="install-tibetan-fonts.sh"
              variant="primary"
            >
              📥 Download Installation Script
            </Button>
          </div>
          <div className="mt-6 p-6 bg-gray-50 rounded-lg border border-gray-200">
            <p className="font-medium text-gray-900 mb-3">After downloading, open Terminal and run:</p>
            <CodeBlock language="bash">
              {`cd ~/Downloads
chmod +x install-tibetan-fonts.sh
./install-tibetan-fonts.sh`}
            </CodeBlock>
          </div>
        </div>
      </Section>

      <Section title="Manual Font Installation">
        <Card title="macOS" variant="bordered">
          <ol>
            <li>Download the font files (.ttf or .otf format)</li>
            <li>Double-click the font file to open Font Book</li>
            <li>Click &ldquo;Install Font&rdquo; button</li>
            <li>The font is now available in all applications</li>
          </ol>
        </Card>

        <Card title="Windows" variant="bordered">
          <ol>
            <li>Download the font files (.ttf or .otf format)</li>
            <li>Right-click the font file and select &ldquo;Install&rdquo;</li>
            <li>Or copy fonts to: <CodeBlock inline>C:\Windows\Fonts</CodeBlock></li>
            <li>Restart applications to see the new fonts</li>
          </ol>
        </Card>

        <Card title="Linux" variant="bordered">
          <ol>
            <li>Download the font files (.ttf or .otf format)</li>
            <li>Copy fonts to: <CodeBlock inline>~/.fonts</CodeBlock> or <CodeBlock inline>/usr/share/fonts</CodeBlock></li>
            <li>Run: <CodeBlock inline>fc-cache -f -v</CodeBlock></li>
            <li>Fonts are now available system-wide</li>
          </ol>
        </Card>
      </Section>

      <Section title="Recommended Tibetan Fonts">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mt-6">
          <Card title="Tibetan Machine Uni" variant="bordered">
            <p className="mb-4">The most widely used Unicode Tibetan font. Clean and readable.</p>
            <Button
              href="https://collab.its.virginia.edu/wiki/tibetan-script/Tibetan%20Machine%20Uni.html"
              variant="secondary"
              size="small"
              target="_blank"
              rel="noopener noreferrer"
            >
              Download from UVA →
            </Button>
          </Card>

          <Card title="Jomolhari" variant="bordered">
            <p className="mb-4">Beautiful Uchen script font with excellent readability.</p>
            <Button
              href="https://collab.its.virginia.edu/wiki/tibetan-script/Jomolhari.html"
              variant="secondary"
              size="small"
              target="_blank"
              rel="noopener noreferrer"
            >
              Download from UVA →
            </Button>
          </Card>

          <Card title="Monlam Uni" variant="bordered">
            <p className="mb-4">Popular font from the Monlam IT Research Centre.</p>
            <Button
              href="https://www.monlam.ai/en/fonts/"
              variant="secondary"
              size="small"
              target="_blank"
              rel="noopener noreferrer"
            >
              Download from Monlam →
            </Button>
          </Card>

          <Card title="DDC Uchen" variant="bordered">
            <p className="mb-4">Traditional Uchen style from the Dzongkha Development Commission.</p>
            <Button
              href="http://www.dzongkha.gov.bt/IT/fonts.html"
              variant="secondary"
              size="small"
              target="_blank"
              rel="noopener noreferrer"
            >
              Download from DDC →
            </Button>
          </Card>
        </div>
      </Section>

      <Section title="Tibetan Keyboard Installation">
        <Card title="macOS" variant="bordered">
          <ol>
            <li>Open <strong>System Settings</strong> (or System Preferences)</li>
            <li>Go to <strong>Keyboard</strong> → <strong>Input Sources</strong></li>
            <li>Click the <strong>+</strong> button</li>
            <li>Select <strong>Tibetan</strong> from the language list</li>
            <li>Choose your preferred keyboard layout:
              <ul>
                <li><strong>Tibetan - Wylie</strong>: Phonetic transliteration</li>
                <li><strong>Tibetan - EWTS</strong>: Extended Wylie</li>
                <li><strong>Tibetan - Tibetan</strong>: Standard keyboard</li>
              </ul>
            </li>
            <li>Click <strong>Add</strong></li>
            <li>Switch keyboards using Control+Space or the menu bar icon</li>
          </ol>
        </Card>

        <Card title="Windows 10/11" variant="bordered">
          <ol>
            <li>Open <strong>Settings</strong> → <strong>Time & Language</strong></li>
            <li>Click <strong>Language & region</strong></li>
            <li>Click <strong>Add a language</strong></li>
            <li>Search for and select <strong>Tibetan</strong></li>
            <li>Click <strong>Next</strong> and then <strong>Install</strong></li>
            <li>Switch keyboards using Windows+Space</li>
          </ol>
        </Card>

        <Card title="Linux (Ubuntu/Debian)" variant="bordered">
          <ol>
            <li>Open <strong>Settings</strong> → <strong>Region & Language</strong></li>
            <li>Under Input Sources, click <strong>+</strong></li>
            <li>Select <strong>Tibetan</strong></li>
            <li>Choose your keyboard layout</li>
            <li>Or install via terminal: <CodeBlock inline>sudo apt-get install ibus-m17n m17n-db</CodeBlock></li>
            <li>Switch keyboards using Super+Space</li>
          </ol>
        </Card>
      </Section>

      <Section title="Using Tibetan Keyboards">
        <SectionHeading as="h3" className="mt-6">
          Wylie Transliteration
        </SectionHeading>
        <p className="text-lg mb-6">
          The Wylie system is the most popular method for typing Tibetan.
          Type phonetically and the text converts to Tibetan script:
        </p>
        
        <div className="my-6 p-8 bg-gradient-to-br from-gray-50 to-white rounded-xl border border-gray-200">
          <div className="flex items-center gap-4 my-4 flex-wrap">
            <CodeBlock inline>om mani padme hung</CodeBlock>
            <span className="text-gray-400 font-bold text-xl">→</span>
            <span className="text-3xl text-gray-900 font-medium">ཨོམ་མ་ནི་པདྨེ་ཧཱུྃ</span>
          </div>
          <div className="flex items-center gap-4 my-4 flex-wrap">
            <CodeBlock inline>bkra shis bde legs</CodeBlock>
            <span className="text-gray-400 font-bold text-xl">→</span>
            <span className="text-3xl text-gray-900 font-medium">བཀྲ་ཤིས་བདེ་ལེགས</span>
          </div>
        </div>

        <SectionHeading as="h3">
          Common Wylie Conventions
        </SectionHeading>
        <ul>
          <li>Use <CodeBlock inline>tsheg</CodeBlock> (space) between syllables: type space for ་</li>
          <li>Stacked consonants: type letters consecutively (e.g., <CodeBlock inline>bkra</CodeBlock> → བཀྲ)</li>
          <li>Vowels: <CodeBlock inline>a</CodeBlock> (default), <CodeBlock inline>i</CodeBlock> (◌ི), <CodeBlock inline>u</CodeBlock> (◌ུ), <CodeBlock inline>e</CodeBlock> (◌ེ), <CodeBlock inline>o</CodeBlock> (◌ོ)</li>
          <li>End with <CodeBlock inline>/</CodeBlock> for shad (།) or <CodeBlock inline>{'//'}</CodeBlock> for double shad (༎)</li>
        </ul>
      </Section>

      <Section title="Additional Resources">
        <ul className="list-none p-0 m-0 space-y-3">
          <li className="pl-6 relative before:content-['→'] before:absolute before:left-0 before:text-gray-400 before:font-bold">
            <a
              href="https://www.thlib.org/tools/scripts/wiki/tibetan%20script.html"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-700 hover:text-gray-900 font-medium transition-colors hover:underline"
            >
              Tibetan & Himalayan Library - Script Resources
            </a>
          </li>
          <li className="pl-6 relative before:content-['→'] before:absolute before:left-0 before:text-gray-400 before:font-bold">
            <a
              href="https://www.studybuddhism.com/en/tibetan-buddhism/tibetan-culture/learn-to-read-tibetan"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-700 hover:text-gray-900 font-medium transition-colors hover:underline"
            >
              Study Buddhism - Learn to Read Tibetan
            </a>
          </li>
          <li className="pl-6 relative before:content-['→'] before:absolute before:left-0 before:text-gray-400 before:font-bold">
            <a
              href="https://collab.its.virginia.edu/wiki/tibetan-script/Tibetan%20Keyboard%20Input%20Methods.html"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-700 hover:text-gray-900 font-medium transition-colors hover:underline"
            >
              UVA - Tibetan Keyboard Input Methods
            </a>
          </li>
          <li className="pl-6 relative before:content-['→'] before:absolute before:left-0 before:text-gray-400 before:font-bold">
            <a
              href="https://www.monlam.ai/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-700 hover:text-gray-900 font-medium transition-colors hover:underline"
            >
              Monlam IT - Tibetan Language Technology
            </a>
          </li>
        </ul>
      </Section>
    </Layout>
  )
}

export default Resources
