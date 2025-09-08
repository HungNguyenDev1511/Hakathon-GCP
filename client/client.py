import asyncio
import os
import json
import re
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv() 

class MCPClientGemini:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

        # Config Gemini
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server"""
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")
            
        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )
        
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        
        await self.session.initialize()
        
        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\n✅ Connected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        """Process a query using Gemini and available tools"""
        response = await self.session.list_tools()
        available_tools = [{
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in response.tools]

        system_prompt = f"""
        You are connected to an MCP server. 
        Available tools: {available_tools}.
        If you need to call a tool, output strictly in format:
        TOOL_CALL: <tool_name> {{...json_args...}}
        Otherwise, just answer normally.
        """

        full_prompt = system_prompt + f"\n\nUser: {query}"

        response = self.model.generate_content(full_prompt)
        text_response = response.text

        # Nếu Gemini yêu cầu gọi tool
        if "TOOL_CALL:" in text_response:
            match = re.search(r"TOOL_CALL:\s*(\w+)\s*(\{.*\})", text_response, re.DOTALL)
            if match:
                tool_name = match.group(1)
                tool_args = json.loads(match.group(2))

                tool_result = await self.session.call_tool(tool_name, tool_args)
                return f"🤖 Gemini decided to call {tool_name}.\nResult:\n{tool_result.content}"

        return text_response

    async def chat_loop(self):
        print("\nMCP Client (Gemini) Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                if query.lower() == 'quit':
                    break
                    
                response = await self.process_query(query)
                print("\n" + response)
                    
            except Exception as e:
                print(f"\nError: {str(e)}")
    
    async def cleanup(self):
        await self.exit_stack.aclose()


async def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python client_gemini.py <path_to_server_script>")
        sys.exit(1)
        
    client = MCPClientGemini()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
