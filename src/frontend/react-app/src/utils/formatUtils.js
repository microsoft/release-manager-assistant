/**
 * Checks if a string appears to be HTML content
 *
 * @param {string} str - The string to check
 * @returns {boolean} - Whether the string appears to be HTML
 */
export const isHTML = (str) => {
  if (!str) return false
  const div = document.createElement('div')
  div.innerHTML = str.trim()
  return div.childNodes.length > 0 && [...div.childNodes].some(node => node.nodeType === 1)
}

/**
 * Processes HTML content to add styling to tables
 *
 * @param {string} htmlContent - The HTML content to process
 * @returns {string} - The processed HTML content
 */
export const processHTMLContent = (htmlContent) => {
  if (!htmlContent) return ''
  const wrapper = document.createElement('div')
  wrapper.innerHTML = htmlContent

  const tables = wrapper.querySelectorAll('table')
  tables.forEach(table => {
    table.classList.add(
      'table-auto', 'border', 'border-gray-400',
      'border-collapse', 'w-full', 'text-sm'
    )

    table.querySelectorAll('th, td').forEach(cell => {
      cell.classList.add('border', 'border-gray-400', 'p-2', 'text-left', 'align-top')
    })
  })

  return wrapper.innerHTML
}

/**
 * Converts markdown to HTML (simplified version of the original implementation)
 * Note: This is a fallback for the ReactMarkdown component
 *
 * @param {string} text - The markdown text to convert
 * @returns {string} - The HTML representation
 */
export const markdownToHTML = (text) => {
  if (!text) return ''

  return text
    .replace(/^##### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^#### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/^\> (.*$)/gim, '<blockquote>$1</blockquote>')
    .replace(/\*\*(.*)\*\*/gim, '<b>$1</b>')
    .replace(/\*(.*)\*/gim, '<i>$1</i>')
    .replace(/!\[(.*?)\]\((.*?)\)/gim, '<img src="$2" alt="$1" class="inline-block max-w-full" />')
    .replace(/\[(.*?)\]\((.*?)\)/gim, '<a href="$2" class="text-blue-600 hover:underline">$1</a>')
    .replace(/\n/gim, '<br />')
}