import { InlineMath, BlockMath } from 'react-katex'
import 'katex/dist/katex.min.css'

type Props = {
  text: string
}

/**
 * 数式と通常テキストを混在させて表示するコンポーネント
 * - $...$ で囲まれた部分はインライン数式（KaTeX）
 * - $$...$$ で囲まれた部分はブロック数式（KaTeX）
 * - それ以外は通常テキスト
 * - 通常テキスト中の \n（改行コード）と "\\n"（バックスラッシュ+n の文字列）は改行として扱う
 */
function MathText({ text }: Props) {
  // $...$ または $$...$$ でテキストを分割
  const parts = text.split(/(\$\$[\s\S]*?\$\$|\$[^$]+\$)/)

  return (
    <>
      {parts.map((part, i) => {
        // ブロック数式
        if (part.startsWith('$$') && part.endsWith('$$')) {
          return <BlockMath key={i} math={part.slice(2, -2)} />
        }
        // インライン数式
        if (part.startsWith('$') && part.endsWith('$')) {
          return <InlineMath key={i} math={part.slice(1, -1)} />
        }
        // 通常テキスト：\n を改行に変換して表示
        return <PlainTextWithLineBreaks key={i} text={part} />
      })}
    </>
  )
}

/**
 * 通常テキスト中の改行を <br /> に変換するヘルパーコンポーネント
 * - 実際の改行コード（\n, \r\n）に対応
 * - LLM が文字列としてリテラル "\n" を返してしまった場合にも対応（保険）
 */
function PlainTextWithLineBreaks({ text }: { text: string }) {
  // まず文字列リテラルとしての "\n" を実際の改行に変換（LLM出力の保険）
  const normalized = text.replace(/\\n/g, '\n')

  // 改行で分割して、間に <br /> を挟む
  const lines = normalized.split('\n')

  return (
    <>
      {lines.map((line, i) => (
        <span key={i}>
          {line}
          {i < lines.length - 1 && <br />}
        </span>
      ))}
    </>
  )
}

export default MathText