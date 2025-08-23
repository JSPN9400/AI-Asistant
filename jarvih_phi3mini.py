import speech_recognition as sr
import pyttsx3
import requests
import json
import sys
import webbrowser
import wikipediaapi
import pywhatkit
import os
import threading
import queue
import time
from typing import List, Callable

# Initialize the text-to-speech engine
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 180)  # Slightly faster speech
tts_engine.setProperty('volume', 0.9)

# Configuration for Ollama API
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "phi3:mini"

# Initialize Wikipedia API
wiki_wiki = wikipediaapi.Wikipedia(
    language='en',
    extract_format=wikipediaapi.ExtractFormat.WIKI,
    user_agent="JarvisAIAssistant/1.0"
)

# Global variables for interruptible speech
speech_queue = queue.Queue()
is_speaking = False
stop_speaking = False

def speak_live(text: str, interruptible: bool = True):
    """Speaks text with interruptible capability like Gemini Live."""
    global is_speaking, stop_speaking
    
    if interruptible:
        stop_speaking = False
    
    is_speaking = True
    print(f"Jarvis: {text}")
    
    # Split text into chunks for more natural speech
    chunks = [chunk.strip() for chunk in text.split('.') if chunk.strip()]
    
    for chunk in chunks:
        if stop_speaking and interruptible:
            print("Jarvis: [Speech interrupted]")
            break
            
        if chunk:
            tts_engine.say(chunk + '.')
            tts_engine.runAndWait()
            time.sleep(0.2)  # Small pause between chunks
    
    is_speaking = False

def interrupt_speech():
    """Interrupt current speech."""
    global stop_speaking
    stop_speaking = True
    tts_engine.stop()

def listen_to_voice_continuous(listening_callback: Callable = None):
    """Listens continuously with real-time interruption capability."""
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.pause_threshold = 0.8
    recognizer.dynamic_energy_threshold = False
    
    with sr.Microphone() as source:
        print("Jarvis: I'm listening... (say 'stop' or 'cancel' to interrupt)")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        
        try:
            while True:
                try:
                    audio = recognizer.listen(source, timeout=1, phrase_time_limit=5)
                    text = recognizer.recognize_google(audio).lower()
                    
                    print(f"You: {text}")
                    
                    # Check for interruption commands
                    if any(cmd in text for cmd in ["stop", "cancel", "never mind", "enough"]):
                        interrupt_speech()
                        return "interrupt"
                    
                    # If callback provided, process immediately
                    if listening_callback:
                        listening_callback(text)
                        
                    return text
                    
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    continue
                except sr.RequestError:
                    return "error"
                    
        except KeyboardInterrupt:
            return "exit"

def get_ai_response_streaming(user_input: str, response_callback: Callable):
    """Streaming response from Ollama with real-time output."""
    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": user_input,
            "stream": True,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 500
            }
        }
        
        response = requests.post(OLLAMA_API_URL, json=payload, stream=True, timeout=60)
        response.raise_for_status()
        
        full_response = ""
        for line in response.iter_lines():
            if line:
                try:
                    json_data = json.loads(line.decode('utf-8'))
                    if 'response' in json_data:
                        chunk = json_data['response']
                        full_response += chunk
                        response_callback(chunk)
                        
                    if json_data.get('done', False):
                        break
                except json.JSONDecodeError:
                    continue
        
        return full_response
        
    except Exception as e:
        response_callback(f"Error: {str(e)}")
        return f"Error: {str(e)}"

def search_wikipedia(query: str) -> str:
    """Search Wikipedia and return summary."""
    try:
        page = wiki_wiki.page(query)
        if page.exists():
            summary = page.summary[:400] + "..." if len(page.summary) > 400 else page.summary
            return f"According to Wikipedia: {summary}"
        return "Sorry, I couldn't find relevant information on Wikipedia."
    except Exception as e:
        return f"Wikipedia search error: {e}"

def search_youtube(query: str):
    """Search and play YouTube video."""
    try:
        speak_live(f"Searching YouTube for {query}", interruptible=False)
        pywhatkit.playonyt(query)
        return f"Playing YouTube results for {query}"
    except Exception as e:
        return f"YouTube search error: {e}"

def open_website(url: str):
    """Open a website in default browser."""
    try:
        webbrowser.open(url)
        return f"Opening {url}"
    except Exception as e:
        return f"Error opening website: {e}"

def open_program(program_name: str) -> str:
    """Open installed program on PC."""
    try:
        program_paths = {
            "chrome": "chrome.exe", "google chrome": "chrome.exe",
            "firefox": "firefox.exe", "edge": "msedge.exe",
            "notepad": "notepad.exe", "calculator": "calc.exe",
            "paint": "mspaint.exe", "word": "winword.exe",
            "excel": "excel.exe", "powerpoint": "powerpnt.exe",
            "vscode": "code.exe", "visual studio code": "code.exe",
            "spotify": "spotify.exe", "discord": "discord.exe"
        }
        
        program_name_lower = program_name.lower()
        
        if program_name_lower in program_paths:
            os.system(f"start {program_paths[program_name_lower]}")
            return f"Opening {program_name}"
        return f"Sorry, I couldn't find {program_name}."
    except Exception as e:
        return f"Error opening program: {e}"

def process_special_command(command: str) -> str:
    """Process special commands before sending to AI."""
    command_lower = command.lower()
    
    if any(keyword in command_lower for keyword in ["wikipedia", "wiki", "what is", "who is"]):
        query = command_lower.replace("search wikipedia for", "").replace("wikipedia", "").replace("wiki", "").replace("what is", "").replace("who is", "").strip()
        return search_wikipedia(query)
    
    elif any(keyword in command_lower for keyword in ["youtube", "play", "watch"]):
        query = command_lower.replace("search youtube for", "").replace("youtube", "").replace("play", "").replace("watch", "").strip()
        return search_youtube(query)
    
    elif any(keyword in command_lower for keyword in ["open website", "go to"]):
        url = "https://" + command_lower.replace("open website", "").replace("go to", "").replace("visit", "").strip() + ".com"
        return open_website(url)
    
    elif any(keyword in command_lower for keyword in ["open", "start", "launch"]):
        program_name = command_lower.replace("open", "").replace("start", "").replace("launch", "").strip()
        return open_program(program_name)
    
    return None

def live_conversation():
    """Main live conversation loop like Gemini Live."""
    print("🎙️  Jarvis Live Mode Activated!")
    print("💬 Talk naturally. Say 'stop' to interrupt, 'exit' to quit.")
    
    while True:
        try:
            # Listen for user input
            user_input = listen_to_voice_continuous()
            
            if user_input == "exit":
                speak_live("Goodbye! Ending live conversation.", interruptible=False)
                break
            elif user_input == "interrupt":
                speak_live("Okay, I stopped.", interruptible=False)
                continue
            elif user_input == "error":
                speak_live("Sorry, I'm having trouble with speech recognition.", interruptible=False)
                continue
            
            # Check for special commands first
            special_response = process_special_command(user_input)
            if special_response:
                speak_live(special_response)
                continue
            
            # Process with AI streaming
            print("Jarvis: ", end="", flush=True)
            
            def stream_callback(chunk):
                print(chunk, end="", flush=True)
                # For true live speech, you'd speak each chunk here
                # but that's complex with interruption handling
            
            full_response = get_ai_response_streaming(user_input, stream_callback)
            print()  # New line after streaming
            
            # Speak the full response with interrupt capability
            speak_live(full_response)
            
        except KeyboardInterrupt:
            speak_live("Goodbye!", interruptible=False)
            break
        except Exception as e:
            print(f"Error: {e}")
            continue

def main():
    """Main menu system."""
    try:
        test_response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if test_response.status_code == 200:
            speak_live("Jarvis initialized successfully. Live mode ready!", interruptible=False)
        else:
            speak_live("Ollama connection issue. Some features may not work.", interruptible=False)
    except:
        speak_live("Cannot connect to Ollama. Basic features only.", interruptible=False)
    
    while True:
        print("\n" + "="*60)
        print("🔊 JARVIS LIVE INTERFACE")
        print("="*60)
        print("1: 🎙️  Live Conversation Mode (Gemini Style)")
        print("2: 📝 Text Command Mode")
        print("3: 📚 Show Available Commands")
        print("4: 🚪 Exit")
        
        choice = input("\nChoose mode (1-4): ").strip()
        
        if choice == '1':
            live_conversation()
        elif choice == '2':
            user_input = input("Enter your command: ").strip()
            if user_input:
                response = process_special_command(user_input) or get_ai_response_streaming(user_input, lambda x: print(x, end="", flush=True))
                speak_live(response)
        elif choice == '3':
            print("\n🎯 AVAILABLE COMMANDS:")
            print("• 'What is quantum computing?' - Wikipedia search")
            print("• 'Play jazz music' - YouTube search")
            print("• 'Open Chrome' - Launch program")
            print("• 'Go to github.com' - Open website")
            print("• Natural conversation - Ask anything!")
            print("\n🎙️ VOICE COMMANDS:")
            print("• 'Stop' or 'Cancel' - Interrupt speech")
            print("• 'Exit' - End conversation")
        elif choice == '4':
            speak_live("Shutting down. Goodbye!", interruptible=False)
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()