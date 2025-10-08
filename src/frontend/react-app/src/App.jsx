import React from 'react'
import Header from './components/Header'
import Chat from './components/Chat'

function App() {
  return (
    <div className="h-screen flex flex-col">
      <Header />
      <Chat />
    </div>
  )
}

export default App