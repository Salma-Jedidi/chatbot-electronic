import json
import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from transformers import AutoModelForCausalLM, AutoTokenizer
import re
import spacy

# Load the NLP model (spaCy)
nlp = spacy.load("en_core_web_sm")  # Small English model

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialisation du tokenizer et du modèle pour ChatGPT
tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium", padding_side='left')
model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")

# Chemins
combined_json_path = r"C:\Users\21623\Desktop\chatbot\recommendationSystem\src\app\flask\conversation.json"

# Charger les données combinées (messages et produits)
def load_combined_data():
    combined_data = {}
    if os.path.exists(combined_json_path):
        with open(combined_json_path, mode='r', encoding='utf-8') as file:
            combined_data = json.load(file)
        return combined_data
    else:
        print(f"Error: The file '{combined_json_path}' does not exist.")
        return {}

# Charger les données
combined_data = load_combined_data()

def get_conversation_response(user_input_lower):
    for message in combined_data["messages"]:
        if user_input_lower in message["user"].lower():
            return message["bot"]
    return None  # Return None if no conversation match

# Parser une plage de prix depuis le texte de l'utilisateur
def parse_price_range(input_text):
    matches = re.findall(r'\d+', input_text)
    if matches:
        # Handle the "under" and "less" cases (both mean the upper bound)
        if 'under' in input_text or 'less' in input_text or 'cheap' in input_text:
            return [0, int(matches[0])]  # Set the upper bound as the matched number
        # Handle the "more" case (this means the lower bound)
        elif 'more' in input_text:
            return [int(matches[0]), float('inf')]  # Set the lower bound as the matched number
        # Handle "between" case, where two numbers are specified
        elif 'between' in input_text:
            return [int(matches[0]), int(matches[1])]  # Use the two numbers as the range
        else:
            # For simple ranges or other price requests (e.g., only one price given)
            return [int(matches[0]), int(matches[0])]  # Treat the same number as both lower and upper
    return None

# Logique de réponse pour les produits
def get_product_response(user_input_lower):
    matched_products = []
    
    # Loop through all products
    for product in combined_data["products"]:
        product_name_lower = product["Product_Name"].lower()
        category_name_lower = product["Category_Name"].lower()

        # Check if the product name is mentioned in the input (substring match)
        if product_name_lower in user_input_lower:
            matched_products.append(
                f"Product: {product['Product_Name']}, Category: {product['Category_Name']}, Price: {product['Product_Price']} USD, Description: {product['Product_Description']}\n"
            )
        
        # Check if the category is mentioned (substring match)
        elif category_name_lower in user_input_lower:
            # Check if price-related words are present in the input
            if any(word in user_input_lower for word in ["price", "cheap", "between", "more", "less", "under", "around", "cost"]):
                # Extract price range if mentioned
                price_range = parse_price_range(user_input_lower)
                
                if price_range:
                    # Filter products by price range within the category
                    if float(product['Product_Price']) >= price_range[0] and (len(price_range) == 1 or float(product['Product_Price']) <= price_range[1]):
                        matched_products.append(
                            f"Product: {product['Product_Name']}, Price: {product['Product_Price']} USD, Description: {product['Product_Description']}\n"
                        )
                else:
                    matched_products.append(
                        f"Product: {product['Product_Name']}, Price: {product['Product_Price']} USD, Description: {product['Product_Description']}\n"
                    )
            else:
                # Default behavior when no price-related words are found
                matched_products.append(
                    f"Product: {product['Product_Name']}, Description: {product['Product_Description']}\n"
                )
    
    # Return the results
    if matched_products:
        return "\n".join(matched_products)
    
    return None  # Return None if no product matches

def generate_product_description(product):
    return f"Product: {product['Product_Name']}, Category: {product['Category_Name']}, Price: {product['Product_Price']} USD, Description: {product['Product_Description']}\n"

# Réponse pour la gamme de prix
def get_price_range_response(user_input_lower):
    # Define keywords to identify a price query
    if "price" in user_input_lower or "cheap" in user_input_lower or "budget" in user_input_lower or "between" in user_input_lower:
        try:
            # Parse the price range
            price_range = parse_price_range(user_input_lower)
            if price_range:
                # Optional: Identify category mentioned in the query
                category = None
                for product in combined_data["products"]:
                    if product["Category_Name"].lower() in user_input_lower:
                        category = product["Category_Name"].lower()
                        break
                
                # Filter products by price range and category
                filtered_products = [
                    f" Product: {product['Product_Name']}, Price: {product['Product_Price']} USD"
                    for product in combined_data["products"]
                    if float(product['Product_Price']) >= price_range[0]
                    and float(product['Product_Price']) <= price_range[1]
                    and (category is None or product["Category_Name"].lower() == category)
                ]
                
                # Return filtered products
                if filtered_products:
                    return f"Products in the price range ${price_range[0]} - ${price_range[1]}:I recommend \n" + "\n".join(filtered_products)
                else:
                    return f"No products found in the price range ${price_range[0]} - ${price_range[1]}."
            else:
                return "Could you clarify the price range you're looking for?"
        except Exception as e:
            print(f"Error processing the price range: {e}")
            return "Sorry, I couldn't process the price range. Please try again."
    return None

# Function to detect singular or plural queries
def is_plural(message: str) -> bool:
    return bool(re.search(r"\b\w+s\b", message.lower()))  # Matches any word ending with 's'


# Function to check product availability
def check_product_availability(user_input_lower):
    # Define keywords related to availability
    availability_keywords = ["available", "availability", "buy", "stock", "purchase"]

    # Check if the user's input includes availability-related words
    if any(keyword in user_input_lower for keyword in availability_keywords):
        for product in combined_data["products"]:
            product_name_lower = product["Product_Name"].lower()

            # Check if the product name exists in the user input
            if product_name_lower in user_input_lower:
                if product["Product_Quantity"] > 0:
                    return f"Yes, we have {product['Product_Name']} in stock! "
                else:
                    # Recommend products in the same category with stock available
                    recommendations = [
                        f"{p['Product_Name']} (Price: {p['Product_Price']} USD)"
                        for p in combined_data["products"]
                        if p["Category_Name"].lower() == product["Category_Name"].lower() and p["Product_Quantity"] > 0
                    ]
                    if recommendations:
                        return (
                            f"Sorry, {product['Product_Name']} is out of stock. "
                            f"I recommend: {', '.join(recommendations)}."
                        )
                    else:
                        return f"Unfortunately, {product['Product_Name']} and similar products are currently out of stock."
        return "Could you specify the product you're looking for?"
    return None

# Logique générale pour la réponse du chatbot
def get_chat_response(user_input):
    user_input_lower = user_input.lower()

    availability_response = check_product_availability(user_input_lower)
    if availability_response:
        return availability_response

    # Check if the query is singular or plural using NLP (e.g., looking for plural words like "phones", "products")
    if is_plural(user_input_lower):
        # Handle multiple product queries
        product_response = get_product_response(user_input_lower)
        if product_response:
            return product_response
        return "Could you specify which product you're interested in?"

    # Check if the question concerns a conversation message
    conversation_response = get_conversation_response(user_input_lower)
    if conversation_response:
        return conversation_response

    # Check if the question concerns a product or category
    product_response = get_product_response(user_input_lower)
    if product_response:
        return product_response

    # Check if the question concerns price range
    price_response = get_price_range_response(user_input_lower)
    if price_response:
        return price_response

    # If no match is found, generate a response with DialoGPT
    inputs = tokenizer.encode(user_input + tokenizer.eos_token, return_tensors="pt")
    bot_output = model.generate(inputs, max_length=100, pad_token_id=tokenizer.eos_token_id)
    return tokenizer.decode(bot_output[:, inputs.shape[-1]:][0], skip_special_tokens=True)

@app.route('/api/test/connection', methods=['GET'])
def test_connection():
    print('Received connection test request')
    return jsonify(message='Connection test successful!')

@app.route('/api', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            data = request.get_json()
            msg = data.get("msg", "")
            print(f"Received message: {msg}")
            response = get_chat_response(msg)
            print(f"Sending response: {response}")
            return jsonify(response=response)
        except Exception as e:
            print(f"Error: {str(e)}")
            return jsonify(error=str(e)), 500
    else:
        return render_template('chat/chat.component.html')

@app.route('/assets/<path:path>')
def send_assets(path):
    return send_from_directory('src/assets', path)

@app.errorhandler(Exception)
def handle_error(e):
    return jsonify(error=str(e)), 500

if __name__ == '__main__':
    app.run(port=5001)