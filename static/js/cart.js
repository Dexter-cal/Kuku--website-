const CART_KEY = "richChickenCart";

function loadCart() {
    const saved = localStorage.getItem(CART_KEY);
    return saved ? JSON.parse(saved) : { items: [] };
}

function saveCart(cart) {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
    updateCartCounts();
}

function updateCartCounts() {
    const cart = loadCart();
    const count = cart.items.reduce((sum, item) => sum + item.quantity, 0);
    const total = cart.items.reduce((sum, item) => sum + item.price * item.quantity, 0);

    const countLabels = document.querySelectorAll("#cartCount");
    countLabels.forEach(label => label.textContent = count);

    const totalLabels = document.querySelectorAll("#cartTotal");
    totalLabels.forEach(label => label.textContent = "KES " + total.toLocaleString());
}

function addToCart(name, price, quantity, id) {
    const cart = loadCart();
    const existing = cart.items.find(item => item.id === id);
    if (existing) {
        existing.quantity += quantity;
    } else {
        cart.items.push({ id, name, price, quantity });
    }
    saveCart(cart);

    // Visual feedback
    const btn = event.target;
    const originalText = btn.textContent;
    btn.textContent = "Added!";
    btn.style.background = "#00b894";
    setTimeout(() => {
        btn.textContent = originalText;
        btn.style.background = "";
    }, 1000);
}

function renderCheckout() {
    const cart = loadCart();
    const container = document.getElementById("cartContainer");
    const hiddenInput = document.getElementById("cart_data");
    const totalLabel = document.getElementById("checkoutTotal");

    if (!container) return;

    if (cart.items.length === 0) {
        container.innerHTML = "<p>Your cart is empty.</p>";
        if (hiddenInput) hiddenInput.value = "[]";
        if (totalLabel) totalLabel.textContent = "KES 0";
        return;
    }

    let html = '<div class="cart-items-list">';
    cart.items.forEach(item => {
        html += `
            <div class="cart-row" style="display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid #eee;">
                <span>${item.quantity}x ${item.name}</span>
                <span>KES ${(item.price * item.quantity).toLocaleString()}</span>
                <button onclick="removeFromCart(${item.id})" style="background:none; border:none; color:red; cursor:pointer;"><i class="fas fa-trash"></i></button>
            </div>
        `;
    });
    html += '</div>';

    container.innerHTML = html;
    const total = cart.items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    if (totalLabel) totalLabel.textContent = "KES " + total.toLocaleString();
    if (hiddenInput) hiddenInput.value = JSON.stringify(cart.items);
}

function removeFromCart(id) {
    const cart = loadCart();
    cart.items = cart.items.filter(item => item.id !== id);
    saveCart(cart);
    renderCheckout();
}

// Payment Selection
function selectPaymentMethod(method) {
    document.getElementById("payment_method").value = method;
    document.getElementById("selectedMethodLabel").textContent = method;
    document.getElementById("checkoutSubmit").disabled = false;

    document.querySelectorAll(".payment-method").forEach(card => card.classList.remove("selected"));
    document.getElementById(method.toLowerCase() + "-card").classList.add("selected");
}

// Simulated STK Push
function handleCheckout(event) {
    const method = document.getElementById("payment_method").value;
    if (method === "M-PESA") {
        event.preventDefault();
        const phone = document.getElementById("phone").value;
        if (!phone) {
            alert("Please enter your phone number.");
            return;
        }

        // Show simulation modal
        const modal = document.createElement("div");
        modal.id = "payment-modal";
        modal.style = "position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:2000; display:flex; justify-content:center; align-items:center; color:white; text-align:center; padding:20px;";
        modal.innerHTML = `
            <div>
                <i class="fas fa-mobile-alt" style="font-size:4rem; color:#4caf50; margin-bottom:20px;"></i>
                <h2>STK Push Sent!</h2>
                <p>Please check your phone (<strong>${phone}</strong>) and enter your M-Pesa PIN to authorize the payment.</p>
                <div class="loader" style="margin:20px auto; border:4px solid #f3f3f3; border-top:4px solid #ff6600; border-radius:50%; width:40px; height:40px; animation:spin 2s linear infinite;"></div>
                <p><small>Waiting for confirmation...</small></p>
            </div>
        `;
        document.body.appendChild(modal);

        // Clear cart after success simulation
        setTimeout(() => {
            localStorage.removeItem(CART_KEY);
            document.querySelector(".checkout-form").submit();
        }, 4000);
    } else {
        // Clear cart for other methods too on submit
        localStorage.removeItem(CART_KEY);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    updateCartCounts();
    renderCheckout();

    const form = document.querySelector(".checkout-form");
    if (form) {
        form.addEventListener("submit", handleCheckout);
    }
});

// Animation for loader
if (!document.getElementById("cart-styles")) {
    const style = document.createElement('style');
    style.id = "cart-styles";
    style.innerHTML = `
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    .payment-method.selected { border: 2px solid var(--primary) !important; background: var(--accent-soft) !important; }
    `;
    document.head.appendChild(style);
}
