import { ReferenceItem } from '@/api/lightrag'
import { FileTextIcon } from 'lucide-react'
import Badge from '@/components/ui/Badge'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/Tooltip'
import { useTranslation } from 'react-i18next'

interface ReferenceListProps {
  references?: ReferenceItem[]
  onReferenceClick?: (reference: ReferenceItem) => void
}

export const ReferenceList = ({ references, onReferenceClick }: ReferenceListProps) => {
  const { t } = useTranslation()
  if (!references || references.length === 0) return null

  return (
    <div className="border-border/50 mt-2 flex flex-wrap gap-2 border-t pt-2">
      <div className="text-muted-foreground mb-1 w-full text-xs">
        {t('retrievePanel.chatMessage.references.sources')}
      </div>
      {references.map((ref) => (
        <TooltipProvider key={ref.reference_id}>
          <Tooltip>
            <TooltipTrigger asChild>
              <Badge
                variant="outline"
                className="hover:bg-accent flex cursor-pointer items-center gap-1 px-2 py-1 transition-colors"
                onClick={() => onReferenceClick?.(ref)}
              >
                <FileTextIcon className="text-muted-foreground size-3" />
                <span className="max-w-[150px] truncate">{ref.file_path.split('/').pop()}</span>
              </Badge>
            </TooltipTrigger>
            <TooltipContent side="bottom" className="max-w-xs break-all">
              <p>{ref.file_path}</p>
              {ref.content && (
                <div className="mt-1 text-[10px] opacity-70">
                  {t('retrievePanel.chatMessage.references.viewInParent')}
                </div>
              )}
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      ))}
    </div>
  )
}
