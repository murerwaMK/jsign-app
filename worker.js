// Basic Cloudflare Worker in JavaScript
export default {
  async fetch(request, env, ctx) {
    // Get the request method and URL
    const { method, url } = request;
    const { pathname } = new URL(url);
    
    // Handle different routes
    if (pathname === '/') {
      return new Response('Hello from Cloudflare Worker!', {
        headers: { 'Content-Type': 'text/plain' }
      });
    }
    
    if (pathname === '/json') {
      const data = {
        message: 'Hello World',
        timestamp: new Date().toISOString(),
        method: method
      };
      
      return new Response(JSON.stringify(data), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    if (pathname === '/api/example' && method === 'POST') {
      try {
        const body = await request.json();
        
        // Process the data
        const response = {
          received: body,
          processed: true,
          timestamp: new Date().toISOString()
        };
        
        return new Response(JSON.stringify(response), {
          headers: { 
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*' // CORS if needed
          }
        });
      } catch (error) {
        return new Response('Invalid JSON', { 
          status: 400,
          headers: { 'Content-Type': 'text/plain' }
        });
      }
    }
    
    // Handle external API calls
    if (pathname === '/proxy') {
      try {
        const externalResponse = await fetch('https://jsonplaceholder.typicode.com/posts/1');
        const data = await externalResponse.json();
        
        return new Response(JSON.stringify(data), {
          headers: { 'Content-Type': 'application/json' }
        });
      } catch (error) {
        return new Response('Failed to fetch external data', { 
          status: 500,
          headers: { 'Content-Type': 'text/plain' }
        });
      }
    }
    
    // 404 for unknown routes
    return new Response('Not Found', { 
      status: 404,
      headers: { 'Content-Type': 'text/plain' }
    });
  }
};