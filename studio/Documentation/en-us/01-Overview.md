# 00 - Overview

Studio (CodeCraft IDE) is a web IDE for Informix 4GL with:
- Monaco editor with support for 4GL, PER, Python, SQL, FM2, and CSS
- 4GL execution via backend
- 4GL <-> Python conversion
- Compilation with 4make
- Local and remote (SFTP) file explorer
- Integrated database tools (schema, queries, terminal)
- Form preview (.per) and Lycia editor (.fm2)

Basic requirements:
- Backend at http://localhost:8000
- Studio at http://localhost:9002

Quick example (typical flow):
1) Open a .4gl
2) Edit
3) Run to execute
4) See output in Console

Known limitations:
- Features depend on the backend being online
- Some features require database drivers installed on the backend

