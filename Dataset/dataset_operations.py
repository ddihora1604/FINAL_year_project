import pandas as pd
import os

def replace_product_placeholder(input_csv_path: str, output_csv_path: str):
    """
    Replace {product_purchased} placeholder in Ticket Description with actual product name.
    
    Args:
        input_csv_path: Path to the input CSV file
        output_csv_path: Path to save the updated CSV file
    """
    try:
        # Read the CSV file
        print(f"Reading CSV file from: {input_csv_path}")
        df = pd.read_csv(input_csv_path)
        
        print(f"Total rows: {len(df)}")
        
        # Check if required columns exist
        if 'Ticket Description' not in df.columns or 'Product Purchased' not in df.columns:
            print("Error: Required columns 'Ticket Description' or 'Product Purchased' not found!")
            return None
        
        # Counter for replacements
        replacement_count = 0
        
        # Replace {product_purchased} with actual product name for each row
        for idx, row in df.iterrows():
            if pd.notna(row['Ticket Description']) and pd.notna(row['Product Purchased']):
                original_description = str(row['Ticket Description'])
                product_name = str(row['Product Purchased'])
                
                # Replace the placeholder
                updated_description = original_description.replace('{product_purchased}', product_name)
                
                # Update the dataframe
                df.at[idx, 'Ticket Description'] = updated_description
                
                # Count if replacement was made
                if original_description != updated_description:
                    replacement_count += 1
        
        print(f"\nReplacements made: {replacement_count} rows")
        
        # Save to new CSV file
        df.to_csv(output_csv_path, index=False)
        
        print(f"Successfully saved updated file to: {output_csv_path}")
        
        return df
        
    except FileNotFoundError:
        print(f"Error: File not found at {input_csv_path}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def main():
    # Define paths
    input_csv = r"C:\Tejas\BE Project\CODEBASE\BE-Project\Dataset\customer_support_tickets_4330.csv"
    output_csv = r"c:\Tejas\BE Project\CODEBASE\BE-Project\Dataset\customer_support_tickets_updated.csv"
    
    # Replace placeholders
    result = replace_product_placeholder(input_csv, output_csv)
    
    if result is not None:
        print("\n" + "="*50)
        print("Sample of updated descriptions:")
        print("="*50)
        # Show a few examples of updated descriptions
        print(result[['Product Purchased', 'Ticket Description']].head(3))
        print("\nProcess completed successfully!")


if __name__ == "__main__":
    main()
