from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter(prefix='/heartbeat', tags=['heartbeat'])


@router.get('/', status_code=status.HTTP_200_OK)
def heartbeat():
    return JSONResponse({'status': 'ok'})
