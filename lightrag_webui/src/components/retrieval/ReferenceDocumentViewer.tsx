import { useState, useEffect, useMemo } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription
} from '@/components/ui/Dialog'
import { getDocumentContent, getHighlights, ReferenceItem } from '@/api/lightrag'
import { LoaderIcon, ExternalLinkIcon, SearchIcon, SparklesIcon } from 'lucide-react'
import { ScrollArea } from '@/components/ui/ScrollArea'
import { toast } from 'sonner'
import Button from '@/components/ui/Button'
import { useTranslation } from 'react-i18next'
import { cn } from '@/lib/utils'

interface ReferenceDocumentViewerProps {
  reference: ReferenceItem | null
  query: string | null
  onClose: () => void
}

export const ReferenceDocumentViewer = ({
  reference,
  query,
  onClose
}: ReferenceDocumentViewerProps) => {
  const { t } = useTranslation()
  const [content, setContent] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [highlightedSentences, setHighlightedSentences] = useState<string[]>([])
  const [isHighlighting, setIsHighlighting] = useState(false)

  useEffect(() => {
    if (!reference) {
      setContent(null)
      setHighlightedSentences([])
      return
    }

    const fetchContentAndHighlights = async () => {
      setIsLoading(true)
      try {
        const docId = reference.doc_id || reference.reference_id
        const data = await getDocumentContent(docId)
        setContent(data.content)

        // If query is provided, fetch semantic highlights
        if (query && data.content) {
          setIsHighlighting(true)
          try {
            const highlights = await getHighlights({
              query,
              context: data.content,
              threshold: 0.5 // Default threshold
            })
            setHighlightedSentences(highlights.highlighted_sentences)
          } catch (hErr) {
            console.error('Failed to fetch semantic highlights:', hErr)
            // Fallback to chunks if highlighting fails
            setHighlightedSentences([])
          } finally {
            setIsHighlighting(false)
          }
        }
      } catch (err) {
        console.error('Failed to fetch document content:', err)
        toast.error('Failed to load document content')
        onClose()
      } finally {
        setIsLoading(false)
      }
    }

    fetchContentAndHighlights()
  }, [reference, query, onClose])

  const highlightedContent = useMemo(() => {
    if (!content) return null

    // Use semantic highlights if available, otherwise fallback to chunks
    const highlightsToUse =
      highlightedSentences.length > 0 ? highlightedSentences : reference?.content || []

    if (highlightsToUse.length === 0) return content

    let result = content
    // Sort chunks by length (descending) to avoid partial matches interfering with larger ones
    const sortedHighlights = [...highlightsToUse].sort((a, b) => b.length - a.length)

    // We'll use a placeholder strategy to avoid multiple highlights on the same text
    const placeholders: string[] = []

    sortedHighlights.forEach((highlight, idx) => {
      const placeholder = `__HL_${idx}__`
      // Try to find the highlight in the content
      if (result.includes(highlight)) {
        placeholders[idx] = highlight
        result = result.split(highlight).join(placeholder)
      }
    })

    // Now replace placeholders with actual marked content
    let finalResult: (string | JSX.Element)[] = [result]

    placeholders.forEach((originalText, idx) => {
      if (!originalText) return
      const placeholder = `__HL_${idx}__`

      const newPieces: (string | JSX.Element)[] = []
      finalResult.forEach((piece) => {
        if (typeof piece !== 'string') {
          newPieces.push(piece)
          return
        }

        const parts = piece.split(placeholder)
        parts.forEach((part, pIdx) => {
          newPieces.push(part)
          if (pIdx < parts.length - 1) {
            const isSemantic = highlightedSentences.length > 0
            newPieces.push(
              <mark
                key={`hl-${idx}-${pIdx}`}
                className={cn(
                  'text-foreground rounded border-b-2 px-0.5 font-medium shadow-sm',
                  isSemantic
                    ? 'border-blue-400 bg-blue-100 dark:border-blue-600 dark:bg-blue-900/40'
                    : 'border-yellow-400 bg-yellow-100 dark:border-yellow-600 dark:bg-yellow-900/40'
                )}
              >
                {originalText}
              </mark>
            )
          }
        })
      })
      finalResult = newPieces
    })

    return finalResult
  }, [content, reference, highlightedSentences])

  return (
    <Dialog open={!!reference} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="border-border/40 flex max-h-[90vh] max-w-4xl flex-col overflow-hidden p-0 shadow-2xl backdrop-blur-sm">
        <DialogHeader className="bg-muted/30 border-b p-6 pb-2">
          <div className="flex items-center justify-between">
            <div className="space-y-1 pr-4">
              <DialogTitle className="flex items-center gap-2 text-xl font-bold">
                <div className="bg-primary/10 text-primary rounded-md p-1.5">
                  <ExternalLinkIcon className="size-4" />
                </div>
                <span className="truncate">{reference?.file_path.split('/').pop()}</span>
              </DialogTitle>
              <DialogDescription className="truncate font-mono text-xs opacity-60">
                {reference?.file_path}
              </DialogDescription>
            </div>
            {highlightedSentences.length > 0 && (
              <div className="flex shrink-0 items-center gap-2 rounded-full border border-blue-200 bg-blue-100 px-3 py-1 text-xs font-medium text-blue-700 dark:border-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
                <SparklesIcon className="size-3" />
                {t(
                  'retrievePanel.chatMessage.references.semanticallyHighlighted',
                  'Semantically Highlighted'
                )}
              </div>
            )}
            {highlightedSentences.length === 0 && reference?.content && (
              <div className="flex shrink-0 items-center gap-2 rounded-full border border-yellow-200 bg-yellow-100 px-3 py-1 text-xs font-medium text-yellow-700 dark:border-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300">
                <SearchIcon className="size-3" />
                {t('retrievePanel.chatMessage.references.chunksHighlighted', {
                  count: reference.content.length
                })}
              </div>
            )}
          </div>
        </DialogHeader>

        <div className="relative min-h-0 flex-1">
          {isLoading ? (
            <div className="bg-background/50 absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 backdrop-blur-sm">
              <LoaderIcon className="text-primary size-8 animate-spin opacity-60" />
              <p className="text-muted-foreground animate-pulse text-sm font-medium">
                {t('retrievePanel.chatMessage.references.loading')}
              </p>
            </div>
          ) : content ? (
            <ScrollArea className="h-full">
              <div className="prose dark:prose-invert max-w-none p-8">
                <div className="text-foreground/90 selection:bg-primary/20 font-sans text-[15px] leading-relaxed whitespace-pre-wrap">
                  {highlightedContent}
                </div>
              </div>
            </ScrollArea>
          ) : (
            <div className="text-muted-foreground flex items-center justify-center p-12 italic">
              {t('retrievePanel.chatMessage.references.noContent')}
            </div>
          )}
        </div>
        <div className="bg-muted/20 flex justify-end gap-2 border-t p-4">
          <Button variant="outline" size="sm" onClick={onClose}>
            {t('common.cancel')}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
