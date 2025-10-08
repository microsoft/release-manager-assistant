import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { isHTML, processHTMLContent } from '../utils/formatUtils'

const Message = ({ message }) => {
  const { text, sender, isFinal, imageUrl } = message

  // If it's an image message
  if (imageUrl) {
    return (
      <div className="w-full flex justify-start">
        <img
          src={imageUrl}
          className="w-full max-w-full h-auto rounded-lg shadow"
          alt="Response visual"
        />
      </div>
    )
  }

  const hasHTML = text && isHTML(text)

  return (
    <div className={`flex ${sender === 'user' ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`
          ${hasHTML ? 'w-full' : 'max-w-[75%] whitespace-pre-wrap'}
          ${sender === 'user'
            ? 'bg-blue-100 text-blue-900'
            : isFinal
              ? 'bg-gray-200 text-gray-900'
              : 'bg-yellow-50 text-yellow-800 text-sm italic border border-yellow-200'}
          px-4 py-2 rounded-lg overflow-x-auto
          ${hasHTML && sender === 'bot' && isFinal ? 'max-h-[500px] min-h-[200px] overflow-y-auto' : ''}
          ${!isFinal && sender === 'bot' ? 'animate-pulse' : ''}
        `}
      >
        {!isFinal && sender === 'bot' && (
          <span className="inline-block w-2 h-2 bg-yellow-500 rounded-full mr-2 animate-bounce"></span>
        )}
        {hasHTML ? (
          <div dangerouslySetInnerHTML={{ __html: processHTMLContent(text) }} />
        ) : (
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {text || ''}
          </ReactMarkdown>
        )}
      </div>
    </div>
  )
}

export default Message