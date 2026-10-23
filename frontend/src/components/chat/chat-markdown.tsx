/** A chat answer as Markdown (TASK-0085): GitHub-flavoured, no raw HTML (react-markdown escapes it) and only
 *  http(s)/mailto links, which open in a new tab. Fenced code uses the shadcn Code Block. */
import Markdown, { type Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { CodeBlock, CodeBlockActions, CodeBlockContent, CodeBlockCopyButton, CodeBlockHeader, CodeBlockLine, CodeBlockTitle } from '@/components/ui/code-block'
import { useHighlightedCode } from '@/hooks/use-highlighted-code'
import { safeUrl } from '@/lib/chat'


function Code({ value, language }: { value: string; language: string }) {
  const lines = useHighlightedCode(value, language || 'text')
  return <CodeBlock size="sm" className="my-2" data-testid="chat-code">
    <CodeBlockHeader><CodeBlockTitle>{language || 'text'}</CodeBlockTitle><CodeBlockActions><CodeBlockCopyButton value={value} /></CodeBlockActions></CodeBlockHeader>
    <CodeBlockContent>{lines.map((l, i) => <CodeBlockLine key={i}>{l}</CodeBlockLine>)}</CodeBlockContent>
  </CodeBlock>
}

const components: Components = {
  pre: ({ children }) => <>{children}</>,
  code: ({ className, children }) => {
    const lang = /language-([\w-]+)/.exec(className || '')?.[1]; const text = String(children ?? '')
    return lang || text.includes('\n') ? <Code value={text} language={lang ?? ''} /> : <code className="rounded bg-muted px-1 py-0.5 font-mono text-[0.85em]">{children}</code>
  },
  a: ({ href, children }) => <a href={href} target="_blank" rel="noopener noreferrer nofollow" className="text-primary underline underline-offset-3">{children}</a>,
  img: ({ alt }) => <span className="text-muted-foreground">[{alt}]</span>,   // no remote images in a chat answer
  ul: ({ children }) => <ul className="list-disc space-y-1 pl-5">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal space-y-1 pl-5">{children}</ol>,
  table: ({ children }) => <div className="my-2 overflow-x-auto"><table className="w-full border-collapse text-xs [&_td]:border [&_td]:px-2 [&_td]:py-1 [&_th]:border [&_th]:bg-muted [&_th]:px-2 [&_th]:py-1">{children}</table></div>,
  blockquote: ({ children }) => <blockquote className="border-l-2 pl-3 text-muted-foreground">{children}</blockquote>,
}

export function ChatMarkdown({ text }: { text: string }) {
  return <div className="space-y-2 [&_h1]:text-base [&_h1]:font-semibold [&_h2]:font-semibold [&_h3]:font-medium" data-testid="chat-markdown">
    <Markdown remarkPlugins={[remarkGfm]} skipHtml urlTransform={safeUrl} components={components}>{text}</Markdown></div>
}
