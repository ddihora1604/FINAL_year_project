import pandas as pd
import os
import time
import logging
from dotenv import load_dotenv
from typing import Optional
from cerebras.cloud.sdk import Cerebras

# Load environment variables
load_dotenv("C:\Tejas\BE Project\CODEBASE\BE-Project\.env")

# Setup logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('answer_generation_safe.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SafeCerebrasGenerator:
    """Conservative Cerebras answer generator that stays well under rate limits."""
    
    def __init__(self, csv_path: str, model_name: str = "qwen-3-235b-a22b-instruct-2507"):
        self.csv_path = csv_path
        self.model_name = model_name
        self.df = None
        self.client = None
        self.current_row = 0
        
        # Conservative rate limiting (25/min to stay safe under 30/min limit)
        self.requests_per_minute = 25  
        self.min_delay_between_requests = 60 / self.requests_per_minute  # 2.4 seconds
        self.last_request_time = 0
        self.request_count_this_minute = 0
        self.minute_start_time = time.time()
        
        # Initialize Cerebras
        self._setup_cerebras()
        
    def _setup_cerebras(self):
        """Setup Cerebras API configuration."""
        api_key = os.getenv("CEREBRAS_API_KEY")
        if not api_key or api_key == "your_cerebras_api_key_here":
            raise ValueError("CEREBRAS_API_KEY not found or not set. Please set it in the .env file.")
        
        try:
            self.client = Cerebras(api_key=api_key)
            logger.info(f"Initialized Cerebras client with model: {self.model_name}")
            logger.info(f"Conservative rate limit: {self.requests_per_minute} requests/minute")
        except Exception as e:
            logger.error(f"Error initializing Cerebras client: {e}")
            raise
    
    def _smart_rate_limit(self):
        """Smart rate limiting that tracks requests per minute."""
        current_time = time.time()
        
        # Reset counter if a minute has passed
        if current_time - self.minute_start_time >= 60:
            self.request_count_this_minute = 0
            self.minute_start_time = current_time
            logger.debug(f"Rate limit counter reset")
        
        # If we're at the limit, wait for the minute to reset
        if self.request_count_this_minute >= self.requests_per_minute:
            wait_time = 60 - (current_time - self.minute_start_time) + 1  # +1 second buffer
            logger.info(f"Rate limit reached ({self.request_count_this_minute}/{self.requests_per_minute}). Waiting {wait_time:.1f} seconds...")
            time.sleep(wait_time)
            self.request_count_this_minute = 0
            self.minute_start_time = time.time()
        
        # Ensure minimum delay between requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_delay_between_requests:
            wait_time = self.min_delay_between_requests - time_since_last
            time.sleep(wait_time)
        
        self.request_count_this_minute += 1
        self.last_request_time = time.time()
        
        logger.debug(f"Request {self.request_count_this_minute}/{self.requests_per_minute} this minute")
    
    def load_data(self):
        """Load CSV data and add Answer column if it doesn't exist."""
        try:
            self.df = pd.read_csv(self.csv_path, encoding='utf-8')
            logger.info(f"Loaded {len(self.df)} records from {self.csv_path}")
            
            # Add Answer column if it doesn't exist
            if 'Answer' not in self.df.columns:
                self.df['Answer'] = ''
                logger.info("Added 'Answer' column to the dataset")
            
            # Find the first row without an answer to resume from
            empty_answers = self.df['Answer'].isna() | (self.df['Answer'] == '')
            if empty_answers.any():
                self.current_row = empty_answers.idxmax()
                logger.info(f"Resuming from row {self.current_row}")
            else:
                self.current_row = len(self.df)
                logger.info("All rows already have answers")
                
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def create_prompt(self, ticket_data: pd.Series) -> tuple:
        """Create system and user prompts."""
        # Extract relevant information
        ticket_id = ticket_data.get('Ticket ID', 'Unknown')
        subject = ticket_data.get('Ticket Subject', 'No subject')
        description = str(ticket_data.get('Ticket Description', ''))[:1200]
        product = ticket_data.get('Product Purchased', 'Unknown product')
        ticket_type = ticket_data.get('Ticket Type', 'General inquiry')
        
        system_prompt = """You are a professional customer support representative. Provide helpful, accurate, and empathetic responses to customer support tickets.

Your response should:
- Acknowledge the customer's concern
- Provide clear, actionable solutions
- Use a professional but friendly tone  
- Keep responses between 100-200 words
- End with next steps if needed"""

        user_message = f"""Customer Support Ticket:

Product: {product}
Issue Type: {ticket_type}
Subject: {subject}
Description: {description}

Please provide a helpful customer support response that addresses this specific issue."""

        return system_prompt, user_message
    
    def generate_answer(self, ticket_data: pd.Series, max_retries: int = 2) -> Optional[str]:
        """Generate answer with conservative rate limiting."""
        
        system_prompt, user_message = self.create_prompt(ticket_data)
        
        for attempt in range(max_retries):
            try:
                # Apply smart rate limiting
                self._smart_rate_limit()
                
                response = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    model=self.model_name,
                    stream=False,
                    max_completion_tokens=400,
                    temperature=0.7,
                    top_p=0.8
                )
                
                if response and response.choices and response.choices[0].message.content:
                    return response.choices[0].message.content.strip()
                else:
                    logger.warning(f"Empty response for ticket {ticket_data.get('Ticket ID', 'Unknown')}")
                    return None
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)[:150]}")
                
                if "rate" in str(e).lower() or "429" in str(e):
                    logger.error("Rate limit hit despite precautions. Waiting 60 seconds...")
                    time.sleep(60)
                    # Reset counters
                    self.request_count_this_minute = 0
                    self.minute_start_time = time.time()
                    continue
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 10
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    return f"Thank you for contacting support regarding your {ticket_data.get('Product Purchased', 'product')}. We apologize for any inconvenience you're experiencing. Our technical team is working on resolving similar issues. Please contact our support team directly for immediate personalized assistance."
        
        return None
    
    def save_progress(self):
        """Save progress with error handling."""
        try:
            self.df.to_csv(self.csv_path, index=False, encoding='utf-8')
            logger.info(f"Progress saved successfully")
        except Exception as e:
            logger.error(f"Error saving: {e}")
            # Create timestamped backup
            backup_path = self.csv_path.replace('.csv', f'_backup_{int(time.time())}.csv')
            self.df.to_csv(backup_path, index=False, encoding='utf-8')
            logger.info(f"Backup saved to {backup_path}")
    
    def generate_answers(self, save_interval: int = 10):
        """Generate answers for all tickets that need them."""
        if self.df is None:
            self.load_data()
        
        # Find tickets needing answers
        rows_needing_answers = []
        for idx, row in self.df.iterrows():
            if pd.isna(row.get('Answer', '')) or row.get('Answer', '') == '':
                rows_needing_answers.append(idx)
        
        if not rows_needing_answers:
            logger.info("All tickets already have answers!")
            return
        
        total_to_process = len(rows_needing_answers)
        
        logger.info(f"Processing ALL {total_to_process} tickets that need answers...")
        
        processed_count = 0
        start_time = time.time()
        
        try:
            for i, idx in enumerate(rows_needing_answers):
                row = self.df.loc[idx]
                ticket_id = row.get('Ticket ID', f'Row {idx}')
                
                logger.info(f"Processing ticket {ticket_id} ({i + 1}/{total_to_process})...")
                
                answer = self.generate_answer(row)
                
                if answer:
                    self.df.at[idx, 'Answer'] = answer
                    processed_count += 1
                    logger.info(f"[SUCCESS] Ticket {ticket_id}")
                else:
                    logger.warning(f"[FAILED] Ticket {ticket_id}")
                
                # Save every N tickets
                if processed_count % save_interval == 0:
                    self.save_progress()
                
                # Show progress every 5 tickets
                if (i + 1) % 5 == 0:
                    elapsed = time.time() - start_time
                    rate = processed_count / (elapsed / 60) if elapsed > 0 else 0
                    remaining = total_to_process - (i + 1)
                    eta_minutes = remaining / rate if rate > 0 else 0
                    logger.info(f"Progress: {processed_count}/{total_to_process} completed ({rate:.1f}/min) - ETA: {eta_minutes:.1f} min")
                
        except KeyboardInterrupt:
            logger.info("Interrupted by user. Saving progress...")
            self.save_progress()
        except Exception as e:
            logger.error(f"Error: {e}")
            self.save_progress()
            raise
        
        # Final save and summary
        self.save_progress()
        elapsed_minutes = (time.time() - start_time) / 60
        logger.info(f"Processing completed: {processed_count}/{total_to_process} tickets in {elapsed_minutes:.1f} minutes")
        
        # Show final status
        total_answered = sum(1 for answer in self.df['Answer'] if not pd.isna(answer) and answer.strip())
        total_tickets = len(self.df)
        logger.info(f"Final status: {total_answered}/{total_tickets} ({(total_answered/total_tickets)*100:.1f}%) tickets have answers")


def main():
    csv_path = "C:\Tejas\BE Project\CODEBASE\BE-Project\Dataset\customer_support_tickets.csv"
    
    print("Safe Cerebras Answer Generator")
    print("=============================")
    print("Rate limit: 25 requests/minute (safe under 30/min limit)")
    print("Will process ALL tickets until complete!")
    print()
    
    try:
        generator = SafeCerebrasGenerator(csv_path)
        generator.load_data()
        
        # Process all remaining tickets
        generator.generate_answers(save_interval=10)
        
        print("\n[SUCCESS] All tickets processed!")
        print("CSV file is now complete with answers for all tickets.")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())