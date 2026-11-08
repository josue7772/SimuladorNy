import streamlit as st
import streamlit.components.v1 as components
import requests
import sqlite3
import numpy as np
import pandas as pd
import json
import math
import os

API_FOOTBALL_KEY = "TU_CLAVE_DE_API_FOOTBALL"
API_BASEBALL_KEY = "TU_CLAVE_DE_API_BASEBALL"
KBO_LEAGUE_ID = "ID_DE_KBO"
