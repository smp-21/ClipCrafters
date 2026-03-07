import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Loader from '../components/ui/Loader.jsx';

export default function VideoEditor() {
  const { id } = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    // Redirect to video detail page for now
    // This can be replaced with actual video editor implementation later
    navigate(`/videos/${id}`, { replace: true });
  }, [id, navigate]);

  return <Loader />;
}
