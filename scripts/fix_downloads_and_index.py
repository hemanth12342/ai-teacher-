# 1. Fix chat.js downloads
with open('frontend/js/chat.js', 'r') as f:
    js = f.read()

# Fix in appendFileMessage
js = js.replace('href="${payload?.url || "#"}"', 'href="${(window.API_BASE_URL || \\'\\') + (payload?.url || \\'#\\')}"')
# Fix in renderFileItem
js = js.replace('href="${file.url || "#"}"', 'href="${(window.API_BASE_URL || \\'\\') + (file.url || \\'#\\')}"')

with open('frontend/js/chat.js', 'w') as f:
    f.write(js)

# 2. Fix index.html reload after setting password
with open('frontend/index.html', 'r') as f:
    html = f.read()

old_block = """                showToast("Password updated successfully!", "success");
                closeEditPasswordModal();
            } catch (e) {"""
new_block = """                showToast("Password updated successfully!", "success");
                closeEditPasswordModal();
                loadClassrooms();
            } catch (e) {"""
html = html.replace(old_block, new_block)

with open('frontend/index.html', 'w') as f:
    f.write(html)

print("Fixes applied.")
