#!/usr/bin/env python3
"""
Basic Python Application Template
=================================

This is a foundational Python application that demonstrates:
- Proper project structure
- Basic logging setup
- Error handling
- Input/output operations
- Placeholder functions for future development

Author: Generated Application
Date: August 06, 2025
"""

import sys
import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Set up logging configuration for the application.
    
    Args:
        log_level (str): The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Set up logging to both file and console
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler(f"{log_dir}/app.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized successfully")
    return logger


def get_user_input(prompt: str, input_type: type = str) -> Optional[Any]:
    """
    Get user input with type validation and error handling.
    
    Args:
        prompt (str): The prompt message to display to the user
        input_type (type): The expected type of input (str, int, float, etc.)
    
    Returns:
        Optional[Any]: The validated user input or None if invalid
    """
    try:
        user_input = input(f"{prompt}: ").strip()
        
        if not user_input:
            return None
        
        if input_type == str:
            return user_input
        elif input_type == int:
            return int(user_input)
        elif input_type == float:
            return float(user_input)
        else:
            return input_type(user_input)
            
    except ValueError as e:
        logger.error(f"Invalid input type. Expected {input_type.__name__}: {e}")
        return None
    except KeyboardInterrupt:
        logger.info("User interrupted input")
        return None


def process_data(data: Any) -> Dict[str, Any]:
    """
    Process input data and return results.
    This is a placeholder function for future data processing logic.
    
    Args:
        data (Any): Input data to process
    
    Returns:
        Dict[str, Any]: Processed data results
    """
    try:
        logger.info(f"Processing data: {data}")
        
        # Placeholder processing logic
        result = {
            "input_data": data,
            "processed_at": datetime.now().isoformat(),
            "status": "success",
            "data_type": type(data).__name__
        }
        
        logger.info("Data processing completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        return {
            "input_data": data,
            "processed_at": datetime.now().isoformat(),
            "status": "error",
            "error_message": str(e)
        }


def save_results(results: Dict[str, Any], filename: Optional[str] = None) -> bool:
    """
    Save processing results to a file.
    
    Args:
        results (Dict[str, Any]): Results to save
        filename (Optional[str]): Output filename, defaults to timestamped file
    
    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"results_{timestamp}.txt"
        
        # Create output directory if it doesn't exist
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Results saved at: {datetime.now().isoformat()}\n")
            f.write("=" * 50 + "\n")
            for key, value in results.items():
                f.write(f"{key}: {value}\n")
        
        logger.info(f"Results saved to {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving results: {e}")
        return False


def display_menu() -> None:
    """Display the main application menu."""
    print("\n" + "="*50)
    print("         BASIC PYTHON APPLICATION")
    print("="*50)
    print("1. Process text data")
    print("2. Process numeric data")
    print("3. View application info")
    print("4. Exit")
    print("="*50)


def get_application_info() -> Dict[str, str]:
    """
    Get basic application information.
    
    Returns:
        Dict[str, str]: Application metadata
    """
    return {
        "name": "Basic Python Application",
        "version": "1.0.0",
        "author": "Generated Application",
        "created": "August 06, 2025",
        "python_version": sys.version,
        "platform": sys.platform
    }


def main_loop() -> None:
    """Main application loop with menu-driven interface."""
    logger.info("Starting main application loop")
    
    while True:
        try:
            display_menu()
            choice = get_user_input("Select an option (1-4)", int)
            
            if choice is None:
                print("Invalid input. Please enter a number between 1 and 4.")
                continue
            
            if choice == 1:
                # Process text data
                text_data = get_user_input("Enter text to process")
                if text_data:
                    results = process_data(text_data)
                    print(f"\nProcessing Results:")
                    for key, value in results.items():
                        print(f"  {key}: {value}")
                    
                    save_choice = get_user_input("Save results to file? (y/n)")
                    if save_choice and save_choice.lower() == 'y':
                        save_results(results)
                
            elif choice == 2:
                # Process numeric data
                numeric_data = get_user_input("Enter a number to process", float)
                if numeric_data is not None:
                    results = process_data(numeric_data)
                    print(f"\nProcessing Results:")
                    for key, value in results.items():
                        print(f"  {key}: {value}")
                    
                    save_choice = get_user_input("Save results to file? (y/n)")
                    if save_choice and save_choice.lower() == 'y':
                        save_results(results)
                
            elif choice == 3:
                # Display application info
                info = get_application_info()
                print(f"\nApplication Information:")
                for key, value in info.items():
                    print(f"  {key}: {value}")
                
            elif choice == 4:
                # Exit application
                print("Thank you for using the Basic Python Application!")
                logger.info("Application terminated by user")
                break
                
            else:
                print("Invalid choice. Please select a number between 1 and 4.")
                
        except KeyboardInterrupt:
            print("\n\nApplication interrupted by user")
            logger.info("Application interrupted by user (Ctrl+C)")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            logger.error(f"Unexpected error in main loop: {e}")


def main() -> int:
    """
    Main entry point of the application.
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    try:
        # Initialize logging
        global logger
        logger = setup_logging(os.getenv("LOG_LEVEL", "INFO"))
        
        # Display startup message
        print("Initializing Basic Python Application...")
        logger.info("Application starting up")
        
        # Get application info
        app_info = get_application_info()
        logger.info(f"Running {app_info['name']} v{app_info['version']}")
        
        # Start main application loop
        main_loop()
        
        # Cleanup and exit
        logger.info("Application shutdown completed successfully")
        return 0
        
    except Exception as e:
        print(f"Critical error: {e}")
        if 'logger' in globals():
            logger.critical(f"Critical application error: {e}")
        return 1


if __name__ == "__main__":
    """Entry point when script is run directly."""
    exit_code = main()
    sys.exit(exit_code)
