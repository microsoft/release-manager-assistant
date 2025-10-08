# Release Manager Assistant Frontend

A React-based frontend for the Release Manager Assistant.

## Features

- Real-time chat interface
- WebSocket communication with the backend
- Markdown and HTML rendering support
- Support for inline images

## Getting Started

### Prerequisites

- Node.js (v14.0.0 or higher)
- npm (v6.0.0 or higher)

### Installation

1. Navigate to the project directory:

   ```bash
   cd src/frontend/react-app
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

### Development

To start the development server:

```bash
npm run dev
```

This will start the Vite development server and open the application in your default browser. The server will reload automatically when you make changes to the code.

### Building for Production

To build the application for production:

```bash
npm run build
```

This will create a production-ready build in the `dist` directory.

### Preview Production Build

To preview the production build:

```bash
npm run preview
```

## Project Structure

- `src/components/` - React components
  - `Header.jsx` - Application header
  - `Chat.jsx` - Main chat container with WebSocket logic
  - `MessageList.jsx` - Message list container
  - `Message.jsx` - Individual message component
  - `InputForm.jsx` - Message input form
- `src/utils/` - Utility functions
  - `formatUtils.js` - Markdown and HTML processing utilities

## Backend Communication

The application communicates with the Release Manager Assistant backend via WebSocket connection to `ws://127.0.0.1:5000/api/query`. Make sure the backend server is running on port 5000 before using the application.

## License

Copyright (c) Microsoft Corporation. Licensed under the MIT license.