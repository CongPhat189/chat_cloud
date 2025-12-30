document.addEventListener("DOMContentLoaded", function () {

// =======================
  // GLOBAL STATE
  // =======================
  let timeout = null;
  let currentChatUserId = null;
  let currentConversationId = null;
  let selectedImages = [];
  let selectedFiles = [];

  const searchInput = document.querySelector(".search-box input");
  const clearBtn = document.querySelector(".clear-search");
  const userList = document.getElementById("user-list");
  const chatList = document.getElementById("chat-list");

  const input = document.getElementById("chat-input-field");
  const messageBox = document.getElementById("chat-messages");
  const previewContainer = document.querySelector(".image-preview-container");

  // =======================
  // SEND MESSAGE (ENTER)
  // =======================
  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();

      const text = input.value.trim();
      if (
          !currentConversationId ||
          (!text && selectedImages.length === 0 && selectedFiles.length === 0)
        ) return;

      sendMessage(text);
      input.value = "";
    }
  });

function sendMessage(text) {
  const tempId = "tmp_" + Date.now();

    // IMAGE PREVIEW
    if (selectedImages.length > 0) {
      const tempUrls = selectedImages.map(f => URL.createObjectURL(f));
      appendMyMessage(tempUrls, true, tempId, "image");
    }

    // FILE PREVIEW
    if (selectedFiles.length > 0) {
      appendMyMessage(
        selectedFiles.map(f => ({ name: f.name })),
        false,
        tempId,
        "file"
      );
    }

    // TEXT
    if (selectedImages.length === 0 && selectedFiles.length === 0) {
      appendMyMessage(text, false, tempId, "text");
    }

    const formData = new FormData();
    formData.append("conversation_id", currentConversationId);

    // ƯU TIÊN FILE → IMAGE → TEXT
    if (selectedFiles.length > 0) {
      formData.append("type", "file");
      selectedFiles.forEach(f => formData.append("files", f));
    }
    else if (selectedImages.length > 0) {
      formData.append("type", "image");
      selectedImages.forEach(img => formData.append("images", img));
    }
    else {
      formData.append("type", "text");
      formData.append("content", text);
    }

  selectedImages = [];
  document.querySelectorAll(".image-preview").forEach(e => e.remove());

  fetch("/api/send-message", {
    method: "POST",
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      if (data.type === "image") {
        replaceTempImages(tempId, data.content);
      }
      else if (data.type === "file") {
        replaceTempFiles(tempId, data.content);
       }
       else {
        replaceTempText(tempId, data.content);
      }
        selectedFiles = [];
        selectedImages = [];
        previewContainer.innerHTML = "";
        })
    .catch(console.error);
}

function replaceTempImages(tempId, realUrls) {
  const msg = document.querySelector(`[data-temp-id="${tempId}"]`);
  if (!msg) return;

  const imgs = msg.querySelectorAll("img");
  imgs.forEach((img, i) => {
    img.src = realUrls[i];
    img.parentElement.classList.remove("loading");
  });
}

function replaceTempText(tempId, text) {
  const msg = document.querySelector(`[data-temp-id="${tempId}"]`);
  if (!msg) return;

  const content = msg.querySelector(".message-content");
  content.textContent = text;

  msg.removeAttribute("data-temp-id");
}

function replaceTempFiles(tempId, realFiles) {
  const msg = document.querySelector(`[data-temp-id="${tempId}"]`);
  if (!msg) return;

  const container = msg.querySelector(".message-files");
  if (!container) return;

  container.innerHTML = realFiles.map(f => `
    <div class="file-wrapper" style="position: relative; display: inline-block;">
      <a href="${f.url}" target="_blank" class="file-item">
        <div class="file-icon">
          <img src="https://cdn-icons-png.flaticon.com/128/4726/4726038.png">
        </div>
        <div class="file-info">
          <div class="file-name" title="${f.name}">${f.name}</div>
          <div class="file-meta">
            <img src="https://cdn-icons-png.flaticon.com/128/3385/3385353.png" title="Đã có trên Cloud">
            <span>Đã có trên Cloud</span>
          </div>
        </div>
      </a>
      <!-- Ô vuông trắng bên phải -->
      <div class="file-action-box">
        <img src="https://cdn-icons-png.flaticon.com/128/3502/3502477.png" alt="Action">
      </div>
    </div>
  `).join("");
}





function appendMyMessage(content, isLoading = false, tempId = null, type = "text") {
  const div = document.createElement("div");
  div.className = "message message-send";
  if (tempId) div.dataset.tempId = tempId;

  let html = "";

  // ===== IMAGE =====
  if (type === "image" && Array.isArray(content)) {
    html += `<div class="message-images">`;
    content.forEach(url => {
      html += `
        <div class="image-wrap ${isLoading ? "loading" : ""}">
          <img src="${url}" class="chat-image">
        </div>
      `;
    });
    html += `</div>`;
  }

  // ===== FILE =====
else if (type === "file" && Array.isArray(content)) {
  html += `<div class="message-files">`;

  content.forEach(f => {
    html += `
      <div class="file-wrapper" style="position: relative; display: inline-block;">
        <a href="${f.url}" target="_blank" class="file-item">
          <div class="file-icon">
            <img src="https://cdn-icons-png.flaticon.com/128/4726/4726038.png">
          </div>
          <div class="file-info">
            <div class="file-name" title="${f.name}">${f.name}</div>
            <div class="file-meta">
              <img src="https://cdn-icons-png.flaticon.com/128/3385/3385353.png" title="Đã có trên Cloud">
              <span>Đã có trên Cloud</span>
            </div>
          </div>
        </a>
        <!-- Ô vuông trắng bên phải -->
        <div class="file-action-box">
          <img src="https://cdn-icons-png.flaticon.com/128/3502/3502477.png" alt="Action">
        </div>
      </div>
    `;
  });

  html += `</div>`;
}





  // ===== TEXT =====
  else {
    html += `<div class="message-content">${content}</div>`;
  }

  div.innerHTML = html;
  messageBox.appendChild(div);
  messageBox.scrollTop = messageBox.scrollHeight;
}




function loadMessages(conversationId) {
  fetch(`/api/messages/${conversationId}`)
    .then(res => res.json())
    .then(messages => {
      messageBox.innerHTML = "";

      messages.forEach(m => {
        const div = document.createElement("div");
        div.className =
          m.sender_id == ME_USER_ID
            ? "message message-send"
            : "message message-receive";

        let html = "";

        // TEXT
        if (m.type === "text" && m.content) {
          html += `<div class="message-content">${m.content}</div>`;
        }

        // IMAGE
        if (m.type === "image" && Array.isArray(m.content)) {
          html += `<div class="message-images">`;
          m.content.forEach(url => {
            html += `<img src="${url}" class="chat-image">`;
          });
          html += `</div>`;
        }
        // FILE
if (m.type === "file" && Array.isArray(m.content)) {
  html += `<div class="message-files">`;

  m.content.forEach(f => {
    html += `
      <div class="file-wrapper" style="position: relative; display: inline-block;">
        <a href="${f.url}" target="_blank" class="file-item">
          <div class="file-icon">
            <img src="https://cdn-icons-png.flaticon.com/128/4726/4726038.png">
          </div>
          <div class="file-info">
            <div class="file-name" title="${f.name}">${f.name}</div>
            <div class="file-meta">
              <img src="https://cdn-icons-png.flaticon.com/128/3385/3385353.png" title="Đã có trên Cloud">
              <span>Đã có trên Cloud</span>
            </div>
          </div>
        </a>
        <!-- Ô vuông trắng bên phải -->
        <div class="file-action-box">
          <img src="https://cdn-icons-png.flaticon.com/128/3502/3502477.png" alt="Action">
        </div>
      </div>
    `;
  });

  html += `</div>`;
}





        div.innerHTML = html;
        messageBox.appendChild(div);
      });

      messageBox.scrollTop = messageBox.scrollHeight;
    });
}


  // =======================
  // SEARCH USER
  // =======================
  if (searchInput) {
    searchInput.addEventListener("input", function () {
      clearTimeout(timeout);

      const phone = this.value.trim();
      clearBtn.style.display = phone ? "block" : "none";

      if (!phone) {
        userList.innerHTML = "";
        userList.style.display = "none";
        chatList.style.display = "block";
        return;
      }

      chatList.style.display = "none";
      userList.style.display = "block";

      timeout = setTimeout(() => {
        fetch(`/api/search-users?phone=${phone}`)
          .then(res => res.json())
          .then(users => {
            userList.innerHTML = "";

            if (users.length === 0) {
              userList.innerHTML =
                "<p style='padding:10px;color:#888'>Không tìm thấy</p>";
              return;
            }

            users.forEach(user => {
              userList.innerHTML += `
                <div class="user-item"
                     data-user-id="${user.user_id}"
                     data-username="${user.username}"
                     data-avatar="${user.avatar || ""}">
                  <div class="user-avatar">
                    ${user.avatar
                      ? `<img src="${user.avatar}">`
                      : `<i class="fa-solid fa-user"></i>`}
                  </div>
                  <div class="user-info">
                    <div class="user-name">${user.username}</div>
                    <div class="user-phone">
                      Số điện thoại: <span>${user.phone}</span>
                    </div>
                  </div>
                </div>`;
            });
          });
      }, 300);
    });
  }

  // CLEAR SEARCH
  clearBtn?.addEventListener("click", function () {
    searchInput.value = "";
    userList.innerHTML = "";
    userList.style.display = "none";
    clearBtn.style.display = "none";
    chatList.style.display = "block";
  });

  // CLICK USER (SEARCH)
  userList.addEventListener("click", function (e) {
    const item = e.target.closest(".user-item");
    if (!item) return;

    openChat({
      user_id: item.dataset.userId,
      username: item.dataset.username,
      avatar: item.dataset.avatar
    });
  });



  // =====================
  // OPEN CHAT
  // =====================
  function openChat(user) {
    currentChatUserId = user.user_id;
    currentConversationId = null;
    input.disabled = true;

    document.querySelector(".chat-header-name").textContent = user.username;
    document.querySelector(".chat-header-avatar img").src =
      user.avatar || "/static/default-avatar.png";

    messageBox.innerHTML =
      `<div class="message message-receive">
        <div class="message-content">Đang tải cuộc trò chuyện...</div>
      </div>`;
        loadFriendStatus(user.user_id);

    fetch("/api/conversations/private", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_a: ME_USER_ID,
        user_b: user.user_id
      })
    })
      .then(res => res.json())
      .then(data => {
        currentConversationId = data.conversation_id;
        input.disabled = false;
        loadMessages(currentConversationId);
      });
  }

  // =============================
  // LOAD CHAT LIST
  // =============================
  function loadChatList() {
    fetch("/api/chat-list")
      .then(res => res.json())
      .then(list => {
        chatList.innerHTML = "";

        if (list.length === 0) {
          chatList.innerHTML =
            "<p style='padding:10px;color:#888'>Chưa có cuộc trò chuyện</p>";
          return;
        }

        list.forEach((u, index) => {
          chatList.innerHTML += `
            <div class="chat-item ${index === 0 ? "active" : ""}"
                 data-user-id="${u.user_id}"
                 data-username="${u.username}"
                 data-avatar="${u.avatar || ""}">
              <div class="chat-avatar">
                <img src="${u.avatar || "/static/default-avatar.png"}">
              </div>
              <div class="chat-info">
                <div class="chat-name">${u.username}</div>
                    <div class="chat-last">
                      ${
                        u.last_message_type === "image"
                          ? `
                            <span class="chat-last-image">
                              <span>Đã gửi:</span>
                              <img src="https://cdn-icons-png.flaticon.com/128/739/739249.png">
                              <span>Hình ảnh</span>
                            </span>
                          `
                          : u.last_message_type === "file"
                            ? `
                              <span class="chat-last-image">
                                <span>Đã gửi:</span>
                                <img src="https://cdn-icons-png.flaticon.com/128/8138/8138518.png">
                                <span>Tệp tin</span>
                              </span>
                            `
                            : (u.last_message || "Chưa có tin nhắn")
                      }
                    </div>
              </div>
            </div>`;
        });

        const first = chatList.querySelector(".chat-item");
        if (first) {
          openChat({
            user_id: first.dataset.userId,
            username: first.dataset.username,
            avatar: first.dataset.avatar
          });
        }
      });
  }

  loadChatList();

  chatList.addEventListener("click", function (e) {
    const item = e.target.closest(".chat-item");
    if (!item) return;

    document.querySelectorAll(".chat-item")
      .forEach(i => i.classList.remove("active"));
    item.classList.add("active");

    openChat({
      user_id: item.dataset.userId,
      username: item.dataset.username,
      avatar: item.dataset.avatar
    });
  });

  // =====================
  // FRIEND ACTION
  // =====================
  function loadFriendStatus(id) {

    const bar = document.querySelector(".friend-request-bar");
    if (!bar) return;

    bar.innerHTML = "";
    bar.onclick = null;
    bar.style.pointerEvents = "auto";

    if (Number(id) === Number(ME_USER_ID)) return;

    fetch(`/api/check-friend?user_id=${id}`)
      .then(res => res.json())
      .then(data => {

        if (data.status === "none") {
          bar.innerHTML = `
            <div class="friend-request-left">
              <img src="https://cdn-icons-png.flaticon.com/128/17847/17847652.png">
              <span>Gửi yêu cầu kết bạn tới người này</span>
            </div>
            <div class="friend-request-right">Gửi kết bạn</div>`;
          bar.querySelector(".friend-request-right").onclick = () => sendFriend(id);
        }

        else if (data.status === "pending") {
          if (data.is_sender) {
            bar.innerHTML = `<div style="margin:auto;color:#dc2626;font-weight:600">Hủy kết bạn</div>`;
            bar.onclick = () => cancelFriend(id);
          } else {
            bar.innerHTML = `
              <div class="friend-request-left">
                <img src="https://cdn-icons-png.flaticon.com/128/17847/17847652.png">
                <span>Người này đã gửi yêu cầu kết bạn</span>
              </div>
              <div class="friend-request-actions">
                <div class="friend-request-accept">Đồng ý</div>
                <div class="friend-request-cancel">Hủy</div>
              </div>`;
            bar.querySelector(".friend-request-accept").onclick = () => acceptFriend(id);
            bar.querySelector(".friend-request-cancel").onclick = () => cancelFriend(id);
          }
        }

        else if (data.status === "accepted") {
          bar.innerHTML = `<div style="margin:auto;color:#16a34a;font-weight:600">✓ Đã là bạn bè</div>`;
          bar.style.pointerEvents = "none";
        }
      });
  }

  function sendFriend(id) {
    fetch("/api/send-friend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: id })
    }).then(() => {
      loadFriendStatus(id);
      loadChatList();
    });
  }

  function acceptFriend(id) {
    fetch("/api/accept-friend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: id })
    }).then(() => {
      loadFriendStatus(id);
      loadChatList();
    });
  }

  function cancelFriend(id) {
    fetch("/api/cancel-friend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: id })
    }).then(() => {
      loadFriendStatus(id);
      loadChatList();
    });
  }

// =====================
// IMAGE PICK
// =====================
const imageInput = document.createElement("input");
imageInput.type = "file";
imageInput.accept = "image/*";
imageInput.multiple = true;
imageInput.style.display = "none";
document.body.appendChild(imageInput);

document.querySelector(".open-image")
  ?.addEventListener("click", () => imageInput.click());

imageInput.addEventListener("change", () => {
  const files = Array.from(imageInput.files);

  for (let file of files) {
    if (selectedImages.length >= 3) {
      alert("Chỉ được chọn tối đa 3 ảnh");
      break;
    }

    selectedImages.push(file);

    const div = document.createElement("div");
    div.className = "image-preview";
    div.innerHTML = `
      <img src="${URL.createObjectURL(file)}">
      <span>&times;</span>
    `;

    div.querySelector("span").onclick = () => {
      selectedImages = selectedImages.filter(f => f !== file);
      div.remove();
    };

    previewContainer.appendChild(div);
  }

  imageInput.value = "";
});

// =====================
// FILE PICK
// =====================
const fileInput = document.createElement("input");
fileInput.type = "file";
fileInput.multiple = true;
fileInput.style.display = "none";
document.body.appendChild(fileInput);

document.querySelector(".open-file")
  ?.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", () => {
  const files = Array.from(fileInput.files);

  for (let file of files) {
    if (selectedFiles.length >= 3) {
      alert("Chỉ được chọn tối đa 3 file");
      break;
    }

    selectedFiles.push(file);

    const div = document.createElement("div");
    div.className = "file-preview";
    div.innerHTML = `
      <i class="fa-solid fa-file"></i>
      <span class="file-name">${file.name}</span>
      <span class="remove-file">&times;</span>
    `;

    div.querySelector(".remove-file").onclick = () => {
      selectedFiles = selectedFiles.filter(f => f !== file);
      div.remove();
    };

    previewContainer.appendChild(div);
  }

  fileInput.value = "";
});


});
