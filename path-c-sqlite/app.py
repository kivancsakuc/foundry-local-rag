"""Streamlit chat interface for the SQLite-backed RAG assistant.

Run:  streamlit run app.py

The retrieved chunks are shown alongside every answer on purpose. When a RAG system
answers badly, the first question is always whether the right passage was retrieved
at all, and hiding that makes the system impossible to debug.
"""

from __future__ import annotations

import time

import streamlit as st

import config
import models
import rag

st.set_page_config(page_title="Summer School RAG Assistant", page_icon="📚")


@st.cache_resource(show_spinner=False)
def bootstrap():
    """Load the models and the indexed vectors once per session."""
    conn = rag.connect()
    chunks = rag.load_chunks(conn)
    conn.close()

    if not chunks:
        return None, None, []

    embedding_model = models.load_embedding_model(on_progress=lambda pct: None)
    chat_model = models.load_chat_model(on_progress=lambda pct: None)
    return (
        embedding_model.get_embedding_client(),
        chat_model.get_chat_client(),
        chunks,
    )


st.title("📚 Summer School RAG Assistant")
st.caption(
    f"Offline · embeddings via `{config.EMBEDDING_MODEL}` · "
    f"chat via `{config.CHAT_MODEL}` · vectors in SQLite"
)

with st.spinner("Loading models and vectors…"):
    embedding_client, chat_client, chunks = bootstrap()

if not chunks:
    st.error(
        f"No indexed chunks found in {config.DB_PATH}.\n\n"
        "Run `python ingest.py` first."
    )
    st.stop()

doc_count = len({c.source for c in chunks})
st.sidebar.metric("Indexed chunks", len(chunks))
st.sidebar.metric("Source documents", doc_count)
top_k = st.sidebar.slider("Chunks retrieved (topK)", 1, 8, config.TOP_K)
st.sidebar.caption(
    "Raise topK if the answer is missing context; lower it if answers get noisy "
    "or slow."
)

if "history" not in st.session_state:
    st.session_state.history = []

for entry in st.session_state.history:
    with st.chat_message(entry["role"]):
        st.markdown(entry["content"])
        if entry.get("sources"):
            with st.expander(f"Retrieved {len(entry['sources'])} chunks"):
                for title, score, content in entry["sources"]:
                    st.markdown(f"**{title}** · similarity `{score:.3f}`")
                    st.text(content)

query = st.chat_input("Ask about the curriculum, the tools, or the architecture…")

if query:
    st.session_state.history.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # Embed the query with the SAME model used at ingest time.
    query_embedding = embedding_client.generate_embedding(query).data[0].embedding

    doc_embeddings = [c.embedding for c in chunks]
    results = rag.find_relevant(query_embedding, doc_embeddings, top_k=top_k)
    retrieved = [chunks[i] for i, _ in results]
    sources = [(chunks[i].title, score, chunks[i].content) for i, score in results]

    messages = rag.build_messages(query, retrieved)

    with st.chat_message("assistant"):
        started = time.perf_counter()

        def stream():
            for chunk in chat_client.complete_streaming_chat(messages):
                # The final chunk carries usage data and an empty choices list.
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content
                if content:
                    yield content

        answer = st.write_stream(stream())
        elapsed = time.perf_counter() - started
        st.caption(f"Answered in {elapsed:.1f}s")

        with st.expander(f"Retrieved {len(sources)} chunks"):
            for title, score, content in sources:
                st.markdown(f"**{title}** · similarity `{score:.3f}`")
                st.text(content)

    st.session_state.history.append(
        {"role": "assistant", "content": answer, "sources": sources}
    )
