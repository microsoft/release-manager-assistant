import React, { useState, useEffect, useRef } from 'react'
import { generateId } from '../utils/idUtils'
import MessageList from './MessageList'
import InputForm from './InputForm'

const Chat = () => {
  const [messages, setMessages] = useState([])
  const [socket, setSocket] = useState(null)
  const interimMessageIdRef = useRef(null)

  const connectWebSocket = () => {
    const sessionId = generateId()
    // Use environment variable for Session Manager URL, fallback to localhost for development
    const sessionManagerUrl = import.meta.env.VITE_SESSION_MANAGER_URL || 'http://127.0.0.1:5000'
    console.log('VITE_SESSION_MANAGER_URL:', import.meta.env.VITE_SESSION_MANAGER_URL)
    console.log('Using Session Manager URL:', sessionManagerUrl)
    
    // Convert HTTP/HTTPS to WS/WSS for WebSocket connections
    let wsUrl
    if (sessionManagerUrl.startsWith('https://')) {
      wsUrl = sessionManagerUrl.replace('https://', 'wss://')
    } else if (sessionManagerUrl.startsWith('http://')) {
      wsUrl = sessionManagerUrl.replace('http://', 'ws://')
    } else {
      wsUrl = sessionManagerUrl
    }
    
    const fullWsUrl = `${wsUrl}/api/query?session_id=${sessionId}`
    console.log('Connecting to WebSocket:', fullWsUrl)
    const ws = new WebSocket(fullWsUrl)

    ws.onopen = () => {
      console.log('WebSocket connection established')
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)

      if (data.error?.error_str) {
        // Clear any interim message on error
        if (interimMessageIdRef.current) {
          setMessages(prev => prev.filter(msg => msg.id !== interimMessageIdRef.current))
          interimMessageIdRef.current = null
        }
        
        addMessage({
          id: generateId(),
          text: 'Error: ' + data.error.error_str,
          sender: 'bot',
          isFinal: true
        })
        return
      }

      if (data.answer?.answer_string) {
        const messageText = data.answer.answer_string
        const isIntermediate = data.answer.is_final === false

        console.log('Received message:', {
          text: messageText,
          is_final: data.answer.is_final,
          isIntermediate,
          currentInterimId: interimMessageIdRef.current
        })

        if (isIntermediate) {
          // This is an intermediate message - replace or create
          if (interimMessageIdRef.current) {
            console.log('Replacing existing intermediate message with ID:', interimMessageIdRef.current)
            // Replace existing intermediate message
            setMessages(prev =>
              prev.map(msg =>
                msg.id === interimMessageIdRef.current
                  ? { ...msg, text: messageText }
                  : msg
              )
            )
          } else {
            // Create new intermediate message
            const newId = generateId()
            console.log('Creating new intermediate message with ID:', newId)
            interimMessageIdRef.current = newId
            addMessage({
              id: newId,
              text: messageText,
              sender: 'bot',
              isFinal: false
            })
          }
        } else {
          // This is a final message - remove ALL intermediate messages
          console.log('Removing all intermediate messages and adding final message')
          
          // Filter out ALL intermediate messages (isFinal: false) and add the final message
          setMessages(prev => {
            const filteredMessages = prev.filter(msg => msg.isFinal !== false)
            return [...filteredMessages, {
              id: generateId(),
              text: messageText,
              sender: 'bot',
              isFinal: true
            }]
          })
          
          // Clear the interim message tracking
          interimMessageIdRef.current = null
        }
      }

      // Handle case where we have a final response (is_final = true) but no answer_string
      // This can happen when only data_points are provided
      if (data.answer && data.answer.is_final !== false && !data.answer.answer_string) {
        console.log('Clearing all intermediate messages due to final response without text')
        setMessages(prev => prev.filter(msg => msg.isFinal !== false))
        interimMessageIdRef.current = null
      }

      if (data.answer?.data_points?.length > 0) {
        addImages(data.answer.data_points)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      
      // Clear any interim message on WebSocket error
      if (interimMessageIdRef.current) {
        setMessages(prev => prev.filter(msg => msg.id !== interimMessageIdRef.current))
        interimMessageIdRef.current = null
      }
      
      addMessage({
        id: generateId(),
        text: 'WebSocket error occurred. Check if the session manager is running on port 5000.',
        sender: 'bot',
        isFinal: true
      })
    }

    ws.onclose = (event) => {
      console.log('WebSocket connection closed:', event.code, event.reason)
      
      // Clear any interim message on WebSocket close
      if (interimMessageIdRef.current) {
        setMessages(prev => prev.filter(msg => msg.id !== interimMessageIdRef.current))
        interimMessageIdRef.current = null
      }
      
      addMessage({
        id: generateId(),
        text: 'WebSocket connection closed.',
        sender: 'bot',
        isFinal: true
      })
    }

    setSocket(ws)
    return ws
  }

  const sendMessage = (text) => {
    if (!text.trim()) return

    // Clear any existing intermediate message when sending a new user message
    if (interimMessageIdRef.current) {
      setMessages(prev => prev.filter(msg => msg.id !== interimMessageIdRef.current))
      interimMessageIdRef.current = null
    }

    addMessage({
      id: generateId(),
      text,
      sender: 'user',
      isFinal: true
    })

    const message = {
      dialog_id: "dialog1",
      message: {
        payload: [
          {
            type: "text",
            value: text
          }
        ]
      }
    }

    if (!socket || socket.readyState !== WebSocket.OPEN) {
      const newSocket = connectWebSocket()

      // Wait for the socket to open before sending
      if (newSocket.readyState === WebSocket.CONNECTING) {
        newSocket.addEventListener('open', () => {
          newSocket.send(JSON.stringify(message))
        })
      }
    } else {
      socket.send(JSON.stringify(message))
    }
  }

  const addMessage = (message) => {
    setMessages(prev => [...prev, message])
  }

  const addImages = (imageSources) => {
    imageSources.forEach(src => {
      addMessage({
        id: generateId(),
        imageUrl: src,
        sender: 'bot',
        isFinal: true
      })
    })
  }

  useEffect(() => {
    return () => {
      // Clean up WebSocket connection when component unmounts
      if (socket) {
        socket.close()
      }
    }
  }, [socket])

  return (
    <main className="flex-1 flex flex-col items-center justify-center px-4 pt-2 pb-20 overflow-hidden">
      <div className="w-full max-w-3xl h-full bg-white shadow-xl rounded-xl flex flex-col overflow-hidden">
        <MessageList messages={messages} />
        <InputForm onSendMessage={sendMessage} />
      </div>
    </main>
  )
}

export default Chat