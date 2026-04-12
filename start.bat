:: Copyright (C) 2026 xhdlphzr
:: This file is part of FranxAgent.
:: FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
:: FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
:: You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

python -m venv .venv
call .\.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
copy config.example.json config.json