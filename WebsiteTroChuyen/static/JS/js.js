document.addEventListener("DOMContentLoaded", function () {

// =======================
  // GLOBAL STATE
  // =======================
  let timeout = null;
  let currentChatUserId = null;
  let currentConversationId = null;
  let selectedImages = [];

  const searchInput = document.querySelector(".search-box input");
  const clearBtn = document.querySelector(".clear-search");
  const userList = document.getElementById("user-list");
  const chatList = document.getElementById("chat-list");

  const input = document.getElementById("chat-input-field");
  const messageBox = document.getElementById("chat-messages");

  // =======================
  // SEND MESSAGE (ENTER)
  // =======================
  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();

      const text = input.value.trim();
      if ((!text && selectedImages.length === 0) || !currentConversationId) return;

      sendMessage(text);
      input.value = "";
    }
  });

  function sendMessage(text) {
    const formData = new FormData();
    formData.append("conversation_id", currentConversationId);
    formData.append("content", text);

    selectedImages.forEach(img => {
      formData.append("images", img);
    });

    fetch("/api/send-message", {
      method: "POST",
      body: formData
    })
      .then(res => res.json())
      .then(data => {
        if (data.error) {
          alert(data.error);
          return;
        }

        selectedImages = [];
        document.querySelectorAll(".image-preview").forEach(e => e.remove());

        appendMyMessage(data.content);
      });
  }

  function appendMyMessage(text) {
    const div = document.createElement("div");
    div.className = "message message-send";
    div.innerHTML = `<div class="message-content">${text}</div>`;
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

          div.innerHTML = `<div class="message-content">${m.content}</div>`;
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
  // OPEN CHAT (CORE)
  // =====================

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
                  ${u.last_message || "Chưa có tin nhắn"}
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
  // FILE / IMAGE PICK
  // =====================

["image", "file"].forEach(type => {
    const inputFile = document.createElement("input");
    inputFile.type = "file";
    if (type === "image") inputFile.accept = "image/*";
    inputFile.style.display = "none";
    document.body.appendChild(inputFile);

    document.querySelector(`.open-${type}`)?.addEventListener("click", () => inputFile.click());

    inputFile.addEventListener("change", () => {
      if (inputFile.files[0]) {
        console.log(`${type} selected:`, inputFile.files[0]);
        inputFile.value = "";
      }
    });
  });

});
