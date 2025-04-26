video-downloader/
├── src/
│   ├── config/
│   │   ├── app.py         # App configuration and constants
│   │   └── constants.py   # Quality maps, user agents, etc.
│   ├── server/
│   │   ├── index.py       # Main application entry point
│   │   ├── models.py      # Database models (User)
│   │   ├── routes/
│   │   │   ├── api.py     # API routes (/preview, /download)
│   │   │   └── pages.py   # Page routes (/, /login, /register)
│   │   ├── services/
│   │   │   ├── download.py  # Common download functionality
│   │   │   ├── youtube.py   # YouTube-specific handling
│   │   │   ├── facebook.py  # Facebook-specific handling
│   │   │   └── tiktok.py    # TikTok-specific handling
│   │   └── utils/
│   │       ├── fileManager.py  # Cache and file management
│   │       └── validators.py   # URL and cookie validation
│   ├── public/
│   │   ├── css/
│   │   │   └── main.css     # Extracted from inline styles
│   │   ├── js/
│   │   │   └── main.js      # Frontend JS (from fe.js)
│   │   └── cookies.txt      # Cookies file
│   └── views/
│       ├── index.html
│       ├── login.html
│       ├── register.html
│       └── partials/
│           ├── header.html  # Common header
│           └── footer.html  # Common footer
└── instance/
    └── users.db            # SQLite database