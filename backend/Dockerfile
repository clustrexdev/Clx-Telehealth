FROM public.ecr.aws/lambda/python:3.10

# Install required system dependencies for WeasyPrint (pango, cairo, etc.)
RUN yum install -y \
    cairo \
    cairo-devel \
    pango \
    pango-devel \
    gdk-pixbuf2 \
    gdk-pixbuf2-devel \
    libffi \
    libffi-devel \
    libxml2 \
    libxslt \
    && yum clean all

# Create directory for ffmpeg
RUN mkdir -p /opt/bin

# Download and install static ffmpeg
RUN yum update -y && \
    yum install -y wget tar xz && \
    wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz && \
    tar -xf ffmpeg-release-amd64-static.tar.xz && \
    cp ffmpeg-*-static/ffmpeg /opt/bin/ && \
    cp ffmpeg-*-static/ffprobe /opt/bin/ && \
    chmod +x /opt/bin/ffmpeg /opt/bin/ffprobe && \
    rm -rf ffmpeg-release-amd64-static.tar.xz ffmpeg-*-static && \
    yum remove -y wget && yum clean all

# Set environment so subprocess finds ffmpeg
ENV PATH="/opt/bin:${PATH}"

# Copy function code and requirements
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD [ "modul.handler" ]
