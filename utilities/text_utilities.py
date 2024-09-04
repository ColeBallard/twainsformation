import tiktoken

class TextUtilities():
    @staticmethod
    def tokenCount(string, encoding_name='cl100k_base'):
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens
    
    @staticmethod
    def segmentText(text, max_length):
        segments = []
        start_index = 0

        while start_index < len(text):
            # Determine the end index for this segment
            end_index = min(start_index + max_length, len(text))
            
            # Find the position of the last period before or at the end index
            period_index = text.rfind('.', start_index, end_index)

            # If no period is found, extend to the next period
            if period_index == -1 or period_index < start_index:
                period_index = text.find('.', end_index)
                if period_index == -1:  # If there's no more periods in the text
                    period_index = len(text) - 1

            # Extract the segment and add to the list
            segment = text[start_index:period_index + 1].strip()
            segments.append(segment)

            # Update the start index for the next segment
            start_index = period_index + 1

        return segments