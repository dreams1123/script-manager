#!/usr/bin/env python3
"""
Script1: Audience Conversation Processor
Monitors MongoDB for pending audience conversations and generates:
- Summary
- 10 Keywords  
- 10 Phrases
Using LLM model: itlwas/hermes-3-llama-3.1-8b
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from utils.llm_server import LLMServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('script1.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AudienceProcessor:
    def __init__(self, llm_base_url="http://localhost:1234"):
        """Initialize the audience processor with MongoDB and LLM connections"""
        self.mongodb_uri = "mongodb+srv://haoga9764:hXbB7fmzpuBJAIr4@cluster0.kmpjdcz.mongodb.net/audience_dropper?retryWrites=true&w=majority&appName=Cluster0"
        self.database_name = "audience_dropper"
        self.collection_name = "audience_conversations"
        
        # Initialize LLM server
        self.llm_server = LLMServer(
            base_url=llm_base_url,
            model_name="itlwas/hermes-3-llama-3.1-8b"
        )
        
        # MongoDB connection
        self.client = None
        self.db = None
        self.collection = None
        
        self.connect_to_mongodb()
    
    def connect_to_mongodb(self) -> bool:
        """Connect to MongoDB and initialize database/collection references"""
        try:
            logger.info("Connecting to MongoDB...")
            self.client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
            
            # Check connection
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
            
            logger.info("Successfully connected to MongoDB")
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            return False
    
    
    def get_pending_conversations(self) -> List[Dict[str, Any]]:
        """Get all conversations with status 'pending'"""
        try:
            pending_conversations = list(self.collection.find({"status": "pending"}))
            logger.info(f"Found {len(pending_conversations)} pending conversations")
            return pending_conversations
        except Exception as e:
            logger.error(f"Error fetching pending conversations: {e}")
            return []
    
    def update_conversation_status(self, conversation_id: str, status: str, additional_data: Dict[str, Any] = None) -> bool:
        """Update conversation status and add additional data"""
        try:
            update_data = {"status": status, "updated_at": datetime.utcnow()}
            if additional_data:
                update_data.update(additional_data)
            
            result = self.collection.update_one(
                {"_id": conversation_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated conversation {conversation_id} status to {status}")
                return True
            else:
                logger.warning(f"No conversation found with ID {conversation_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating conversation status: {e}")
            return False
    
    def process_conversation(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single conversation to generate summary, keywords, and phrases"""
        conversation_id = conversation.get("_id")
        conversation_history = conversation.get("conversation_history", [])
        
        logger.info(f"Processing conversation {conversation_id}")
        
        try:
            # Update status to processing
            self.update_conversation_status(conversation_id, "processing")
            
            # Generate summary from conversation history
            logger.info("Generating summary...")
            summary = self.llm_server.generate_summary(conversation_history)
            
            if not summary:
                logger.error("Failed to generate summary")
                self.update_conversation_status(conversation_id, "failed", {"error": "Failed to generate summary"})
                return {}
            
            # Extract 10 keywords from summary
            logger.info("Extracting keywords...")
            keywords = self.llm_server.extract_keywords(summary)
            
            if not keywords or len(keywords) < 5:
                logger.warning(f"Only got {len(keywords)} keywords, using defaults")
                keywords = [
                    "I need help with", "looking for solutions", "my business is struggling",
                    "need support", "anyone know a good", "recommendations for",
                    "just started", "trying to find", "need advice", "help me with"
                ][:10]
            
            # Generate 10 phrases from keywords
            logger.info("Generating phrases...")
            phrases = self.llm_server.generate_phrases_from_keywords(keywords)
            
            if not phrases or len(phrases) < 5:
                logger.warning(f"Only got {len(phrases)} phrases, using defaults")
                phrases = [
                    "I need help with this situation",
                    "Looking for advice and support", 
                    "Anyone been through something similar?",
                    "My family member is struggling with this",
                    "Seeking recommendations from the community",
                    "Does anyone know where to get help?",
                    "Just diagnosed and need guidance",
                    "Support group recommendations needed",
                    "Looking for treatment options",
                    "Anyone have experience with this?"
                ][:10]
            
            # Prepare results
            results = {
                "summary": summary,
                "keywords": keywords[:10],  # Ensure exactly 10
                "phrases": phrases[:10],    # Ensure exactly 10
                "processed_at": datetime.utcnow(),
                "llm_model": "itlwas/hermes-3-llama-3.1-8b"
            }
            
            # Update conversation with results and mark as completed
            self.update_conversation_status(conversation_id, "completed", results)
            
            logger.info(f"Successfully processed conversation {conversation_id}")
            logger.info(f"Summary length: {len(summary)} characters")
            logger.info(f"Keywords: {len(keywords)}")
            logger.info(f"Phrases: {len(phrases)}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing conversation {conversation_id}: {e}")
            self.update_conversation_status(conversation_id, "failed", {"error": str(e)})
            return {}
    
    def run_monitoring_loop(self, check_interval: int = 30):
        """Run the main monitoring loop"""
        logger.info("Starting audience conversation monitoring...")
        logger.info(f"Check interval: {check_interval} seconds")
        
        # Check LLM server availability
        try:
            if not self.llm_server.test_connection():
                logger.error("LLM server not available. Please start LM Studio with the model loaded.")
                return
        except Exception as e:
            logger.error(f"LLM server connection error: {e}")
            return
        
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while True:
            try:
                # Get pending conversations
                pending_conversations = self.get_pending_conversations()
                
                if pending_conversations:
                    logger.info(f"Processing {len(pending_conversations)} pending conversations...")
                    
                    for conversation in pending_conversations:
                        self.process_conversation(conversation)
                        time.sleep(2)  # Small delay between processing
                else:
                    logger.info("No pending conversations found")
                
                # Reset error counter on successful iteration
                consecutive_errors = 0
                
                # Wait before next check
                logger.info(f"Waiting {check_interval} seconds before next check...")
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Error in monitoring loop (attempt {consecutive_errors}): {e}")
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"Too many consecutive errors ({max_consecutive_errors}). Stopping monitoring.")
                    break
                
                # Wait before retrying
                time.sleep(min(60, check_interval * consecutive_errors))
    
    def process_single_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """Process a single conversation by ID"""
        try:
            conversation = self.collection.find_one({"_id": conversation_id})
            if not conversation:
                logger.error(f"Conversation {conversation_id} not found")
                return {}
            
            return self.process_conversation(conversation)
            
        except Exception as e:
            logger.error(f"Error processing single conversation: {e}")
            return {}
    
    def get_conversation_status(self, conversation_id: str) -> Optional[str]:
        """Get the status of a specific conversation"""
        try:
            conversation = self.collection.find_one({"_id": conversation_id}, {"status": 1})
            return conversation.get("status") if conversation else None
        except Exception as e:
            logger.error(f"Error getting conversation status: {e}")
            return None
    
    def close_connections(self):
        """Close database connections"""
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection")

def main():
    """Main function to run the audience processor"""
    processor = AudienceProcessor()
    
    try:
        # Check if specific conversation ID provided as argument
        if len(sys.argv) > 1:
            conversation_id = sys.argv[1]
            logger.info(f"Processing single conversation: {conversation_id}")
            result = processor.process_single_conversation(conversation_id)
            if result:
                print(json.dumps(result, indent=2, default=str))
        else:
            # Run monitoring loop
            processor.run_monitoring_loop()
    
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        processor.close_connections()

if __name__ == "__main__":
    main()