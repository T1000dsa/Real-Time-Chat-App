from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import Response, RedirectResponse
import time
import logging
from typing import Optional

