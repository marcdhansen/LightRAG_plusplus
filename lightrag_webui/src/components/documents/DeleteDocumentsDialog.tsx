import { useState, useCallback, useEffect } from 'react'
import Button from '@/components/ui/Button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter
} from '@/components/ui/Dialog'
import Input from '@/components/ui/Input'
import { toast } from 'sonner'
import { errorMessage } from '@/lib/utils'
import { deleteDocuments, getDocuments, logToServer } from '@/api/lightrag'

import { TrashIcon, AlertTriangleIcon } from 'lucide-react'
import { useTranslation } from 'react-i18next'

// Simple Label component
const Label = ({
  htmlFor,
  className,
  children,
  ...props
}: React.LabelHTMLAttributes<HTMLLabelElement>) => (
  <label htmlFor={htmlFor} className={className} {...props}>
    {children}
  </label>
)

interface DeleteDocumentsDialogProps {
  selectedDocIds: string[]
  onDocumentsDeleted?: () => Promise<void>
}

export default function DeleteDocumentsDialog({
  selectedDocIds,
  onDocumentsDeleted
}: DeleteDocumentsDialogProps) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  const [confirmText, setConfirmText] = useState('')
  const [deleteFile, setDeleteFile] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [deleteLLMCache, setDeleteLLMCache] = useState(false)
  const isConfirmEnabled = confirmText.toLowerCase() === 'yes' && !isDeleting

  // Reset state when dialog closes
  useEffect(() => {
    if (open) {
      console.log('[DeleteDocumentsDialog] Open with IDs:', selectedDocIds)
      logToServer(
        'info',
        `[DeleteDocumentsDialog] Open with IDs: ${JSON.stringify(selectedDocIds)}`
      )
      setConfirmText('')
      setIsDeleting(false)
    } else {
      // This else block handles the original "reset on close" functionality
      setConfirmText('')
      setDeleteFile(false)
      setDeleteLLMCache(false)
      setIsDeleting(false)
    }
  }, [open, selectedDocIds])

  const handleDelete = useCallback(async () => {
    if (!isConfirmEnabled || selectedDocIds.length === 0) return

    setIsDeleting(true)
    try {
      const result = await deleteDocuments(selectedDocIds, deleteFile, deleteLLMCache)

      if (result.status === 'deletion_started') {
        toast.success(t('documentPanel.deleteDocuments.success', { count: selectedDocIds.length }))
      } else if (result.status === 'busy') {
        toast.error(t('documentPanel.deleteDocuments.busy'))
        setConfirmText('')
        setIsDeleting(false)
        return
      } else if (result.status === 'not_allowed') {
        toast.error(t('documentPanel.deleteDocuments.notAllowed'))
        setConfirmText('')
        setIsDeleting(false)
        return
      } else {
        toast.error(t('documentPanel.deleteDocuments.failed', { message: result.message }))
        setConfirmText('')
        setIsDeleting(false)
        return
      }

      // Close dialog immediately to unblock UI
      setOpen(false)
      setIsDeleting(false)

      // Run polling in background
      ;(async () => {
        // Poll for up to 30 seconds (60 attempts * 500ms)
        const maxAttempts = 60

        for (let i = 0; i < maxAttempts; i++) {
          try {
            // Fetch latest documents with cache busting
            const response = await getDocuments(Date.now())

            const allDocs = Object.values(response.statuses).flat()
            const remainingIds = selectedDocIds.filter((id) => allDocs.some((doc) => doc.id === id))

            if (remainingIds.length === 0) {
              console.log(`[DeleteDocumentsDialog] Deletion confirmed after ${i + 1} checks`)

              // Trigger final update
              if (onDocumentsDeleted) {
                await onDocumentsDeleted()
                toast.success(t('documentPanel.deleteDocuments.complete'))
              }
              return
            }

            if ((i + 1) % 5 === 0) {
              const allDocs = Object.values(response.statuses).flat()
              const remainingDocs = allDocs.filter((doc) => selectedDocIds.includes(doc.id))
              const statuses = remainingDocs.map((d) => `${d.id}(${d.status})`).join(', ')

              const msg = `[DeleteDocumentsDialog] Documents still present: ${statuses}. Waiting... (Attempt ${i + 1}/${maxAttempts})`
              console.log(msg)
              logToServer('info', msg)
            }

            // Wait 500ms before next check
            await new Promise((resolve) => setTimeout(resolve, 500))
          } catch (e) {
            console.error('Error polling document status:', e)
            await new Promise((resolve) => setTimeout(resolve, 500))
          }
        }

        // Timeout fallback
        console.warn('[DeleteDocumentsDialog] Deletion polling timed out')
        if (onDocumentsDeleted) {
          await onDocumentsDeleted()
          toast.warning(t('documentPanel.deleteDocuments.timeout'))
        }
      })()
    } catch (err) {
      toast.error(t('documentPanel.deleteDocuments.error', { error: errorMessage(err) }))
      setConfirmText('')
      setIsDeleting(false)
    }
  }, [isConfirmEnabled, selectedDocIds, deleteFile, deleteLLMCache, setOpen, t, onDocumentsDeleted])

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          variant="destructive"
          side="bottom"
          tooltip={t('documentPanel.deleteDocuments.tooltip', { count: selectedDocIds.length })}
          size="sm"
        >
          <TrashIcon /> {t('documentPanel.deleteDocuments.button')}
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-xl" onCloseAutoFocus={(e) => e.preventDefault()}>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 font-bold text-red-500 dark:text-red-400">
            <AlertTriangleIcon className="h-5 w-5" />
            {t('documentPanel.deleteDocuments.title')}
          </DialogTitle>
          <DialogDescription className="pt-2">
            {t('documentPanel.deleteDocuments.description', { count: selectedDocIds.length })}
          </DialogDescription>
        </DialogHeader>

        <div className="mb-4 font-semibold text-red-500 dark:text-red-400">
          {t('documentPanel.deleteDocuments.warning')}
        </div>

        <div className="mb-4">
          {t('documentPanel.deleteDocuments.confirm', { count: selectedDocIds.length })}
        </div>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="confirm-text" className="text-sm font-medium">
              {t('documentPanel.deleteDocuments.confirmPrompt')}
            </Label>
            <Input
              id="confirm-text"
              value={confirmText}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setConfirmText(e.target.value)}
              placeholder={t('documentPanel.deleteDocuments.confirmPlaceholder')}
              className="w-full"
              disabled={isDeleting}
            />
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="delete-file"
              checked={deleteFile}
              onChange={(e) => setDeleteFile(e.target.checked)}
              disabled={isDeleting}
              className="h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500"
            />
            <Label htmlFor="delete-file" className="cursor-pointer text-sm font-medium">
              {t('documentPanel.deleteDocuments.deleteFileOption')}
            </Label>
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="delete-llm-cache"
              checked={deleteLLMCache}
              onChange={(e) => setDeleteLLMCache(e.target.checked)}
              disabled={isDeleting}
              className="h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500"
            />
            <Label htmlFor="delete-llm-cache" className="cursor-pointer text-sm font-medium">
              {t('documentPanel.deleteDocuments.deleteLLMCacheOption')}
            </Label>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)} disabled={isDeleting}>
            {t('common.cancel')}
          </Button>
          <Button variant="destructive" onClick={handleDelete} disabled={!isConfirmEnabled}>
            {isDeleting
              ? t('documentPanel.deleteDocuments.deleting')
              : t('documentPanel.deleteDocuments.confirmButton')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
