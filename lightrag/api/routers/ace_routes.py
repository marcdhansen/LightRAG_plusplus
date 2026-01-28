import traceback

from fastapi import APIRouter, Depends, HTTPException

from lightrag.utils import logger

from ..utils_api import get_combined_auth_dependency

router = APIRouter(tags=["ace"])


def create_ace_routes(rag, api_key: str | None = None):
    combined_auth = get_combined_auth_dependency(api_key)

    @router.get("/ace/repairs/pending", dependencies=[Depends(combined_auth)])
    async def get_pending_repairs():
        try:
            if not hasattr(rag, "ace_curator") or not rag.ace_curator:
                # ACE might not be enabled
                return []
            return rag.ace_curator.get_pending_repairs()
        except Exception as e:
            logger.error(f"Error getting pending repairs: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=str(e))

    @router.post(
        "/ace/repairs/{repair_id}/approve", dependencies=[Depends(combined_auth)]
    )
    async def approve_repair(repair_id: str):
        try:
            if not hasattr(rag, "ace_curator") or not rag.ace_curator:
                raise HTTPException(
                    status_code=400, detail="ACE Curator not initialized"
                )
            success = await rag.ace_curator.approve_repair(repair_id)
            if not success:
                raise HTTPException(status_code=404, detail="Repair not found")
            return {"status": "success", "message": f"Repair {repair_id} approved"}
        except Exception as e:
            logger.error(f"Error approving repair {repair_id}: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=str(e))

    @router.post(
        "/ace/repairs/{repair_id}/reject", dependencies=[Depends(combined_auth)]
    )
    async def reject_repair(repair_id: str):
        try:
            if not hasattr(rag, "ace_curator") or not rag.ace_curator:
                raise HTTPException(
                    status_code=400, detail="ACE Curator not initialized"
                )
            success = await rag.ace_curator.reject_repair(repair_id)
            if not success:
                raise HTTPException(status_code=404, detail="Repair not found")
            return {"status": "success", "message": f"Repair {repair_id} rejected"}
        except Exception as e:
            logger.error(f"Error rejecting repair {repair_id}: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=str(e))

    return router
