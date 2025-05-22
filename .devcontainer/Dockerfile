# Use an official Python runtime as a parent image
FROM python:3.13

# Set the working directory in the container
#vscode
WORKDIR /workspaces/lead-time-demand
#intellij
# WORKDIR /IdeaProjects/lead-time-demand

# Add necessary repositories and install R along with other packages
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    gfortran \
    wget \
    unzip \
    fontconfig \
    libopenblas-dev \
    liblapack-dev \
    fish \
    curl \
    r-base \
    r-base-dev \
    r-recommended \
    libxml2-dev \
    libssl-dev \
    libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the time zone environment variable
ENV TZ=Europe/Berlin

# Download and install JetBrainsMono Nerd Font
RUN wget -O /tmp/JetBrainsMono.zip https://github.com/ryanoasis/nerd-fonts/releases/download/v2.1.0/JetBrainsMono.zip && \
    unzip /tmp/JetBrainsMono.zip -d /usr/share/fonts && \
    fc-cache -fv && \
    rm /tmp/JetBrainsMono.zip

# Install starship
RUN curl -fsSL https://starship.rs/install.sh | sh -s -- -y || { echo 'Starship installation failed' ; exit 1; }

# Ensure the Python output is set straight to the terminal without buffering it first
ENV PYTHONUNBUFFERED=1

# Copy requirements.txt into the working directory in the container
COPY requirements.txt .

# Install Python dependencies globally
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install jupyter ipykernel rpy2 && \
    python -m ipykernel install --user --name=myenv --display-name "Python (devcontainer)"

# Copy starship config
COPY .devcontainer/starship.toml /root/.config/starship.toml

# Initialize starship in fish
RUN mkdir -p ~/.config/fish && echo 'starship init fish | source' >> ~/.config/fish/config.fish

# Install LaTeX packages
RUN apt-get update && apt-get install -y \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-latex-recommended \
    dvipng \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Set fish as the default shell
SHELL ["/usr/bin/fish", "-c"]

# Expose Jupyter port
EXPOSE 8888

# Set R environment variables
ENV R_HOME=/usr/lib/R
ENV PATH=$PATH:/usr/lib/R/bin

# Test R and Python integration
RUN python3 -c "import rpy2.robjects as robjects; print('R integration successful')"

# Start Jupyter Notebook
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--no-browser", "--allow-root"]